import csv
from datetime import date

from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Turno
from ..pagination import PaginacionEstandar
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


def _parsear_fecha(valor, campo):
    """Convierte 'YYYY-MM-DD' en date; si el formato es inválido, 400 con el
    error en el campo (no un 500 ni un filtro que se ignora en silencio)."""
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ValidationError({campo: 'Usá el formato AAAA-MM-DD.'})


class FiltrosTurnosMixin:
    """Visibilidad y filtros compartidos por el listado y la exportación de
    turnos, para que el CSV exportado sea exactamente lo que se ve en pantalla.

    Parámetros: ?barbero=<id> (solo admin), ?estado=, ?q= (texto sobre el
    cliente), ?fecha_desde= y ?fecha_hasta= (AAAA-MM-DD, ambos inclusivos).
    Un Barbero solo ve su propia agenda aunque manipule ?barbero=."""

    def turnos_filtrados(self):
        params = self.request.query_params
        usuario = self.request.user
        qs = Turno.objects.select_related('cliente__usuario', 'barbero__usuario', 'servicio')

        if usuario.rol == 'admin':
            barbero_id = params.get('barbero')
            if barbero_id:
                qs = qs.filter(barbero_id=barbero_id)
        else:
            barbero = getattr(usuario, 'barbero', None)
            qs = qs.filter(barbero=barbero) if barbero else qs.none()

        estado = params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        q = params.get('q')
        if q:
            qs = qs.filter(
                Q(cliente__usuario__first_name__icontains=q) |
                Q(cliente__usuario__last_name__icontains=q) |
                Q(cliente__usuario__email__icontains=q)
            )

        desde = params.get('fecha_desde')
        hasta = params.get('fecha_hasta')
        desde = _parsear_fecha(desde, 'fecha_desde') if desde else None
        hasta = _parsear_fecha(hasta, 'fecha_hasta') if hasta else None
        if desde and hasta and desde > hasta:
            raise ValidationError({'fecha_hasta': 'Tiene que ser igual o posterior a fecha_desde.'})
        if desde:
            qs = qs.filter(fecha_turno__gte=desde)
        if hasta:
            qs = qs.filter(fecha_turno__lte=hasta)

        return qs.order_by('-fecha_turno', '-hora_inicio')


class TurnosPagination(PaginacionEstandar):
    pass


class TurnosListView(FiltrosTurnosMixin, generics.ListCreateAPIView):
    """GET /api/turnos/?barbero=<id>&estado=&q=&fecha_desde=&fecha_hasta= — Barbero o Admin.
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
        return self.turnos_filtrados()


class TurnosExportarView(FiltrosTurnosMixin, APIView):
    """GET /api/turnos/exportar/ — descarga en CSV los turnos que se ven en
    el listado: acepta los mismos filtros (?barbero=, ?estado=, ?q=,
    ?fecha_desde=, ?fecha_hasta=) y respeta la misma visibilidad (un Barbero
    solo exporta su agenda). Sin paginar: exporta todo lo que matchea."""
    permission_classes = (IsAuthenticated, EsBarberoOAdmin)

    COLUMNAS = (
        'ID', 'Fecha', 'Hora inicio', 'Hora fin', 'Cliente', 'Email del cliente',
        'Barbero', 'Servicio', 'Estado', 'Precio', 'Observaciones',
    )

    @staticmethod
    def _celda(valor):
        """Neutraliza la inyección de fórmulas: Excel interpreta como fórmula
        una celda que empieza con = + - @, y 'observaciones' es texto libre."""
        texto = '' if valor is None else str(valor)
        return "'" + texto if texto[:1] in ('=', '+', '-', '@') else texto

    def get(self, request):
        turnos = self.turnos_filtrados()
        registrar_evento_log(request.user.id, 'exportacion_turnos', {'cantidad': turnos.count()})

        respuesta = HttpResponse(content_type='text/csv; charset=utf-8')
        respuesta['Content-Disposition'] = 'attachment; filename="turnos.csv"'
        respuesta.write('\ufeff')  # BOM: Excel abre bien las tildes
        escritor = csv.writer(respuesta)
        escritor.writerow(self.COLUMNAS)
        for t in turnos:
            escritor.writerow([self._celda(c) for c in (
                t.id,
                t.fecha_turno.strftime('%d/%m/%Y'),
                t.hora_inicio.strftime('%H:%M'),
                t.hora_fin.strftime('%H:%M'),
                t.cliente.usuario.get_display_name(),
                t.cliente.usuario.email,
                t.barbero.usuario.get_display_name(),
                t.servicio.nombre,
                t.get_estado_display(),
                t.precio(),
                t.observaciones,
            )])
        return respuesta


class MisTurnosView(generics.ListAPIView):
    """GET /api/turnos/mis-turnos/?estado= — el Cliente ve sus propios
    turnos (cualquier estado, no excluye cancelados). Existe porque
    TurnosListView es exclusiva de Barbero/Admin (agenda ajena) y el
    Cliente necesita su propio listado para la pantalla 'Mis turnos' del
    frontend, sin poder ver turnos de otros clientes."""
    permission_classes = (IsAuthenticated, EsClienteOAdmin)
    serializer_class = TurnoListSerializer
    pagination_class = TurnosPagination

    def get_queryset(self):
        cliente = getattr(self.request.user, 'cliente', None)
        qs = Turno.objects.select_related('cliente__usuario', 'barbero__usuario', 'servicio')
        qs = qs.filter(cliente=cliente) if cliente else qs.none()

        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

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
