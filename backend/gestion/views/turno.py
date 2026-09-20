from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Turno
from ..permissions import EsBarberoOAdmin, EsClienteOAdmin
from ..serializers import (
    TurnoListSerializer, TurnoCreateSerializer, TurnoUpdateEstadoSerializer,
    ServicioMasSolicitadoSerializer,
)
from ..mongo import registrar_notificacion, registrar_evento_log

# ---------------------------------------------------------------------------
# Gestión de turnos — CU-04/CU-05. RBAC: barbero solo su propia agenda,
# admin control total. El cliente reserva (POST) y cancela lo propio
# (TurnoCancelarView); no puede ver la agenda de nadie.
# ---------------------------------------------------------------------------


def _verificar_ownership(usuario, turno, attr, mensaje):
    """`attr` es 'barbero' o 'cliente': confirma que el perfil propio del
    usuario coincide con turno.<attr>, si no levanta PermissionDenied.
    Usado por TurnoDetailView y TurnoCancelarView, que chequean ownership
    contra distintos actores pero con la misma forma."""
    perfil = getattr(usuario, attr, None)
    if perfil is None or getattr(turno, f'{attr}_id') != perfil.id:
        raise PermissionDenied(mensaje)


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


class TurnosListView(generics.ListCreateAPIView):
    """GET /api/turnos/?barbero=<id>&estado=&q= — Barbero o Admin.
    Un Barbero solo puede ver su propia agenda aunque manipule ?barbero= por
    la URL (RBAC: 'Barbero: reserva de turnos ajenos -> Denegado').
    El Administrador ve todo y puede filtrar por barbero.

    POST /api/turnos/ — el cliente reserva un turno (Cliente o Admin)."""
    pagination_class = TurnosPagination

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), EsClienteOAdmin()]
        return [IsAuthenticated(), EsBarberoOAdmin()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TurnoCreateSerializer
        return TurnoListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        turno = serializer.save()
        registrar_notificacion(
            turno.barbero.usuario_id, 'nuevo_turno',
            f'Tenés un nuevo turno el {turno.fecha_turno:%d/%m} {turno.hora_inicio:%H:%M}.',
        )
        registrar_evento_log(request.user.id, 'creacion_turno', {'turno_id': turno.id})
        return Response(TurnoListSerializer(turno).data, status=status.HTTP_201_CREATED)

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
            _verificar_ownership(usuario, obj, 'barbero', 'No podés modificar turnos de otro barbero.')
        return obj

    def perform_update(self, serializer):
        turno = serializer.save()
        if turno.estado == Turno.Estado.CANCELADO:
            turno.sincronizar_pago_tras_cancelacion()
        registrar_notificacion(
            turno.cliente.usuario_id, 'estado_turno',
            f'Tu turno del {turno.fecha_turno:%d/%m} {turno.hora_inicio:%H:%M} '
            f'ahora está {turno.get_estado_display()}.',
        )
        registrar_evento_log(self.request.user.id, 'cambio_estado_turno', {'turno_id': turno.id, 'estado': turno.estado})


class TurnoCancelarView(APIView):
    """PATCH /api/turnos/<id>/cancelar/ — el cliente cancela su propio turno,
    dentro de la ventana permitida (Turno.puede_cancelar_cliente()). Admin
    puede cancelar cualquiera sin la restricción de ventana ni ownership,
    pero el chequeo de estado (no cancelar algo ya completado/cancelado)
    aplica siempre, admin incluido."""
    permission_classes = (IsAuthenticated, EsClienteOAdmin)

    def patch(self, request, pk):
        turno = get_object_or_404(
            Turno.objects.select_related('cliente__usuario', 'barbero__usuario', 'servicio', 'pago'), pk=pk,
        )
        usuario = request.user

        if usuario.rol != 'admin':
            _verificar_ownership(usuario, turno, 'cliente', 'No podés cancelar turnos de otro cliente.')

        if not turno.es_cancelable():
            raise ValidationError({'detail': 'Este turno ya no se puede cancelar.'})

        if usuario.rol != 'admin':
            if turno.tiene_pago_aprobado():
                raise PermissionDenied(
                    'Este turno ya está pagado — contactá al administrador para '
                    'cancelarlo y gestionar el reembolso.'
                )
            if not turno.puede_cancelar_cliente():
                raise PermissionDenied('Ya no podés cancelar este turno, contactá al administrador.')

        turno.estado = Turno.Estado.CANCELADO
        turno.save(update_fields=['estado'])
        turno.sincronizar_pago_tras_cancelacion()
        registrar_notificacion(
            turno.barbero.usuario_id, 'turno_cancelado',
            f'El turno del {turno.fecha_turno:%d/%m} {turno.hora_inicio:%H:%M} fue cancelado.',
        )
        registrar_evento_log(usuario.id, 'cancelacion_turno', {'turno_id': turno.id})
        return Response(TurnoListSerializer(turno).data)


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
        return Response(ServicioMasSolicitadoSerializer(data, many=True).data)
