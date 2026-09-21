from django.db import IntegrityError
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..models import Resena
from ..pagination import PaginacionEstandar
from ..permissions import EsClienteOAdmin
from ..serializers import ResenaSerializer, ResenaCreateSerializer
from ..mongo import registrar_evento_log

# ---------------------------------------------------------------------------
# Reseñas — calificación del cliente a un turno ya completado.
# ---------------------------------------------------------------------------


class ResenaListCreateView(generics.ListCreateAPIView):
    """GET /api/resenas/?barbero=<id> — público, para mostrar la
    calificación de un barbero. POST — el cliente dueño del turno lo
    califica (turno tiene que estar `completado` y sin reseña previa,
    validado en ResenaCreateSerializer)."""
    pagination_class = PaginacionEstandar

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), EsClienteOAdmin()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ResenaCreateSerializer
        return ResenaSerializer

    def get_queryset(self):
        qs = Resena.objects.select_related('cliente__usuario', 'barbero__usuario')
        barbero_id = self.request.query_params.get('barbero')
        if barbero_id:
            qs = qs.filter(barbero_id=barbero_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        turno = serializer.validated_data['turno']

        usuario = request.user
        if usuario.rol != 'admin':
            cliente = getattr(usuario, 'cliente', None)
            if cliente is None or turno.cliente_id != cliente.id:
                raise PermissionDenied('No podés reseñar un turno de otro cliente.')

        # cliente/barbero salen del turno, no del body ni de quién hace el
        # POST (importa para el caso admin, que no tiene perfil de Cliente).
        try:
            # Resena.turno es OneToOne (constraint único a nivel de base) —
            # si dos POST concurrentes pasan la validación del serializer
            # para el mismo turno, esto es lo que evita que el segundo
            # termine en un 500 (mismo patrón que Pago en el Paquete 4).
            resena = serializer.save(cliente=turno.cliente, barbero=turno.barbero)
        except IntegrityError:
            return Response(
                {'detail': 'Este turno ya tiene una reseña.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        registrar_evento_log(request.user.id, 'creacion_resena', {'resena_id': resena.id, 'turno_id': turno.id})
        return Response(ResenaSerializer(resena).data, status=status.HTTP_201_CREATED)
