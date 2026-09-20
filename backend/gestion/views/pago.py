from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..mercadopago_client import crear_preferencia, obtener_pago, MercadoPagoError
from ..models import Pago, Turno
from ..permissions import EsClienteOAdmin
from ..serializers import PagoSerializer, PagoCreateSerializer
from ..mongo import registrar_notificacion, registrar_evento_log

# ---------------------------------------------------------------------------
# Pagos — integración con Mercado Pago (Checkout Pro), CU-06. POST crea la
# preferencia -> se redirige al cliente al init_point -> MP pega al webhook
# -> el webhook confirma o cancela el turno.
# ---------------------------------------------------------------------------

MAPA_ESTADOS_MP = {
    'approved': Pago.Estado.APROBADO,
    'rejected': Pago.Estado.RECHAZADO,
    'refunded': Pago.Estado.REEMBOLSADO,
    'cancelled': Pago.Estado.RECHAZADO,
    'pending': Pago.Estado.PENDIENTE,
    'in_process': Pago.Estado.PENDIENTE,
}


class PagoListCreateView(generics.ListCreateAPIView):
    """GET /api/pagos/ — el cliente ve los propios, el admin ve todos.
    POST /api/pagos/ — genera el Pago y la preferencia de Mercado Pago para
    un turno propio en estado pendiente."""
    permission_classes = (IsAuthenticated, EsClienteOAdmin)
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PagoCreateSerializer
        return PagoSerializer

    def get_queryset(self):
        usuario = self.request.user
        qs = Pago.objects.select_related('turno__cliente__usuario', 'turno__barbero__usuario')
        if usuario.rol != 'admin':
            cliente = getattr(usuario, 'cliente', None)
            qs = qs.filter(turno__cliente=cliente) if cliente else qs.none()
        return qs.order_by('-fecha_creacion')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        turno = serializer.validated_data['turno']

        usuario = request.user
        if usuario.rol != 'admin':
            cliente = getattr(usuario, 'cliente', None)
            if cliente is None or turno.cliente_id != cliente.id:
                raise PermissionDenied('No podés generar un pago para un turno de otro cliente.')

        try:
            # Turno.pago es OneToOne (constraint único a nivel de base) —
            # si dos POST concurrentes pasan la validación del serializer
            # para el mismo turno, esto es lo que evita que ambos terminen
            # creando un Pago (el segundo choca acá, no con datos duplicados).
            pago = Pago.objects.create(
                turno=turno, monto_total=turno.precio(), metodo_pago=Pago.Metodo.MERCADO_PAGO,
            )
        except IntegrityError:
            return Response(
                {'detail': 'Este turno ya tiene un pago asociado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            preferencia = crear_preferencia(turno)
        except MercadoPagoError as e:
            pago.delete()
            return Response(
                {'detail': f'No se pudo generar el pago en Mercado Pago: {e}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        pago.transaccion_id = preferencia.get('id', '')
        pago.save(update_fields=['transaccion_id'])
        registrar_evento_log(usuario.id, 'creacion_pago', {'pago_id': pago.id, 'turno_id': turno.id})

        return Response({
            'id': pago.id,
            'init_point': preferencia.get('init_point'),
            'estado': pago.estado,
        }, status=status.HTTP_201_CREATED)


class PagoWebhookView(APIView):
    """POST /api/pagos/webhook/ — público, lo llama Mercado Pago. No confía
    en el payload recibido: vuelve a consultar el pago real contra la API de
    MP antes de tocar el estado del Pago/Turno."""
    permission_classes = (AllowAny,)

    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        tipo = payload.get('type') or request.query_params.get('topic')
        payment_id = (payload.get('data') or {}).get('id') or request.query_params.get('id')

        if tipo != 'payment' or not payment_id:
            return Response(status=status.HTTP_200_OK)

        try:
            pago_mp = obtener_pago(payment_id)
        except MercadoPagoError:
            return Response(status=status.HTTP_200_OK)

        turno_id = pago_mp.get('external_reference')
        nuevo_estado = MAPA_ESTADOS_MP.get(pago_mp.get('status'))

        with transaction.atomic():
            # select_for_update(): Mercado Pago reintenta notificaciones
            # ante timeout/5xx, así que dos POST del mismo pago pueden
            # llegar casi juntos — sin el lock, los dos leerían el mismo
            # estado viejo y dispararían la notificación al cliente dos
            # veces (mismo tipo de carrera que ya resolvimos en la creación
            # del turno).
            pago = Pago.objects.select_for_update().select_related(
                'turno__cliente__usuario'
            ).filter(turno_id=turno_id).first()
            if pago is None:
                return Response(status=status.HTTP_200_OK)

            campos = []
            # El id de la preferencia (guardado al crear el Pago) y el id
            # del pago real son entidades distintas en Mercado Pago — acá
            # sí guardamos el id real, el único útil para reconciliar.
            payment_id_real = str(pago_mp.get('id') or '')
            if payment_id_real and payment_id_real != pago.transaccion_id:
                pago.transaccion_id = payment_id_real
                campos.append('transaccion_id')

            estado_cambio = bool(nuevo_estado) and nuevo_estado != pago.estado
            if estado_cambio:
                pago.estado = nuevo_estado
                campos.append('estado')
                if nuevo_estado == Pago.Estado.APROBADO:
                    pago.fecha_pago = timezone.now()
                    campos.append('fecha_pago')

            if campos:
                pago.save(update_fields=campos)

            if estado_cambio:
                turno = pago.turno
                if turno.estado == Turno.Estado.PENDIENTE:
                    if nuevo_estado == Pago.Estado.APROBADO:
                        turno.estado = Turno.Estado.CONFIRMADO
                        turno.save(update_fields=['estado'])
                        registrar_notificacion(
                            turno.cliente.usuario_id, 'pago_aprobado',
                            f'Tu pago del turno del {turno.fecha_turno:%d/%m} fue aprobado.',
                        )
                    elif nuevo_estado == Pago.Estado.RECHAZADO:
                        turno.estado = Turno.Estado.CANCELADO
                        turno.save(update_fields=['estado'])
                        registrar_notificacion(
                            turno.cliente.usuario_id, 'pago_rechazado',
                            f'Tu pago del turno del {turno.fecha_turno:%d/%m} fue rechazado, la reserva se canceló.',
                        )
                registrar_evento_log(None, 'webhook_pago', {'pago_id': pago.id, 'estado': nuevo_estado})

        return Response(status=status.HTTP_200_OK)
