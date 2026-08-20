from datetime import timedelta

from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cliente, Barbero, Servicio, Turno, Pago
from .permissions import EsBarberoOAdmin
from .serializers import (
    RegisterSerializer, LoginSerializer, UsuarioMeSerializer,
    TurnoListSerializer, TurnoUpdateEstadoSerializer,
)
from .mongo import registrar_notificacion, registrar_evento_log


# ---------------------------------------------------------------------------
# Auth — CU-01 Registrar e Iniciar Sesión
# ---------------------------------------------------------------------------

class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — público. RF/REQ-001."""
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        registrar_evento_log(usuario.id, 'registro_usuario', {'email': usuario.email})
        registrar_notificacion(usuario.id, 'bienvenida', 'Bienvenido a Barber Life')
        return Response(
            {'detail': 'Cuenta creada correctamente. Ya podés iniciar sesión.'},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/auth/login/ — público. RF/REQ-002/REQ-003 (login con rol)."""
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.tokens()
        registrar_evento_log(data['usuario']['id'], 'login_exitoso')
        return Response(data, status=status.HTTP_200_OK)


class MeView(APIView):
    """GET /api/auth/me/ — el frontend lo usa para saber el rol del usuario
    logueado y decidir a qué rutas puede navegar (authGuard + roleGuard)."""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(UsuarioMeSerializer(request.user).data)


# ---------------------------------------------------------------------------
# Dashboard — CU-07. RBAC: admin ve ingresos, barbero NO (wiki: "restricción
# financiera para barberos: solo ven volumen de trabajo").
# ---------------------------------------------------------------------------

DIAS_CORTOS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']


class DashboardView(APIView):
    permission_classes = (IsAuthenticated, EsBarberoOAdmin)

    def get(self, request):
        usuario = request.user
        es_admin = usuario.rol == 'admin'

        turnos_qs = Turno.objects.all()
        if not es_admin:
            barbero = getattr(usuario, 'barbero', None)
            if barbero is None:
                return Response(
                    {'detail': 'Tu usuario tiene rol barbero pero no tiene perfil de Barbero asociado. '
                                'Pedile al administrador que lo cree desde /admin/.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            turnos_qs = turnos_qs.filter(barbero=barbero)

        hoy = timezone.localdate()
        turnos_hoy = turnos_qs.filter(fecha_turno=hoy).exclude(estado=Turno.Estado.CANCELADO).count()

        if es_admin:
            clientes_activos = Cliente.objects.filter(activo=True).count()
        else:
            clientes_activos = turnos_qs.values('cliente').distinct().count()

        ingresos_del_mes = None
        if es_admin:
            inicio_mes = hoy.replace(day=1)
            ingresos_del_mes = Pago.objects.filter(
                estado=Pago.Estado.APROBADO,
                fecha_pago__date__gte=inicio_mes,
            ).aggregate(total=Sum('monto_total'))['total'] or 0

        # Turnos por semana: últimos 7 días con datos reales (no placeholder)
        inicio_semana = hoy - timedelta(days=6)
        conteos = (
            turnos_qs.filter(fecha_turno__gte=inicio_semana)
            .exclude(estado=Turno.Estado.CANCELADO)
            .values_list('fecha_turno', flat=True)
        )
        conteo_por_dia = {}
        for fecha in conteos:
            conteo_por_dia[fecha] = conteo_por_dia.get(fecha, 0) + 1
        turnos_por_semana = []
        for i in range(7):
            dia = inicio_semana + timedelta(days=i)
            turnos_por_semana.append({
                'dia': DIAS_CORTOS[dia.weekday()],
                'cantidad': conteo_por_dia.get(dia, 0),
            })

        ultimos_turnos = turnos_qs.exclude(estado=Turno.Estado.CANCELADO).order_by('-fecha_creacion')[:5]
        ultimos_turnos_data = TurnoListSerializer(ultimos_turnos, many=True).data

        return Response({
            'rol': usuario.rol,
            'nombre': usuario.get_full_name() or usuario.email.split('@')[0],
            'turnos_hoy': turnos_hoy,
            'clientes_activos': clientes_activos,
            'ingresos_del_mes': ingresos_del_mes,
            'turnos_por_semana': turnos_por_semana,
            'ultimos_turnos': ultimos_turnos_data,
        })


# ---------------------------------------------------------------------------
# Gestión de turnos — CU-04/CU-05. RBAC: barbero solo su propia agenda,
# admin control total, cliente denegado (matriz de la wiki).
# ---------------------------------------------------------------------------

class TurnosPagination(PageNumberPagination):
    page_size = 7
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'page': self.page.number,
            'num_pages': self.page.paginator.num_pages,
            'results': data,
        })


class TurnosListView(generics.ListAPIView):
    """GET /api/turnos/?barbero=<id>&estado=&q=
    Un Barbero solo puede ver su propia agenda aunque manipule ?barbero= por
    la URL (RBAC: 'Barbero: reserva de turnos ajenos -> Denegado').
    El Administrador ve todo y puede filtrar por barbero."""
    permission_classes = (IsAuthenticated, EsBarberoOAdmin)
    serializer_class = TurnoListSerializer
    pagination_class = TurnosPagination

    def get_queryset(self):
        usuario = self.request.user
        qs = Turno.objects.select_related('cliente__usuario', 'barbero__usuario', 'servicio')

        if usuario.rol == 'admin':
            barbero_id = self.request.query_params.get('barbero')
            if barbero_id:
                qs = qs.filter(barbero_id=barbero_id)
        else:
            barbero = getattr(usuario, 'barbero', None)
            qs = qs.filter(barbero=barbero) if barbero else qs.none()

        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(
                Q(cliente__usuario__first_name__icontains=q) |
                Q(cliente__usuario__last_name__icontains=q) |
                Q(cliente__usuario__email__icontains=q)
            )

        return qs.order_by('-fecha_turno', '-hora_inicio')


class TurnoDetailView(generics.RetrieveUpdateAPIView):
    """PATCH /api/turnos/<id>/ — usado para cancelar o cambiar estado desde
    el menú de acciones de la tabla. Un barbero solo puede tocar sus propios
    turnos (ownership check, no solo rol)."""
    permission_classes = (IsAuthenticated, EsBarberoOAdmin)
    queryset = Turno.objects.select_related('cliente__usuario', 'barbero__usuario', 'servicio')

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return TurnoUpdateEstadoSerializer
        return TurnoListSerializer

    def get_object(self):
        obj = super().get_object()
        usuario = self.request.user
        if usuario.rol != 'admin':
            barbero = getattr(usuario, 'barbero', None)
            if barbero is None or obj.barbero_id != barbero.id:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('No podés modificar turnos de otro barbero.')
        return obj

    def perform_update(self, serializer):
        turno = serializer.save()
        registrar_notificacion(
            turno.cliente.usuario_id, 'estado_turno',
            f'Tu turno del {turno.fecha_turno:%d/%m} {turno.hora_inicio:%H:%M} '
            f'ahora está {turno.get_estado_display()}.',
        )
        registrar_evento_log(self.request.user.id, 'cambio_estado_turno', {'turno_id': turno.id, 'estado': turno.estado})


class ServiciosMasSolicitadosView(APIView):
    """GET /api/turnos/servicios-mas-solicitados/ — panel de la izquierda en
    Gestión de turnos. Cálculo real sobre Turno, no hardcodeado."""
    permission_classes = (IsAuthenticated, EsBarberoOAdmin)

    def get(self, request):
        usuario = request.user
        qs = Turno.objects.exclude(estado=Turno.Estado.CANCELADO)
        if usuario.rol != 'admin':
            barbero = getattr(usuario, 'barbero', None)
            qs = qs.filter(barbero=barbero) if barbero else qs.none()

        ranking = (
            qs.values('servicio_id', 'servicio__nombre', 'servicio__precio')
            .annotate(cantidad=Count('id'))
            .order_by('-cantidad')[:5]
        )
        data = [{
            'servicio_id': r['servicio_id'],
            'nombre': r['servicio__nombre'],
            'precio': r['servicio__precio'],
            'cantidad': r['cantidad'],
        } for r in ranking]
        return Response(data)
