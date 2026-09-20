from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated

from ..models import Barbero
from ..serializers import BarberoPublicSerializer, BarberoDetailSerializer, BarberoMeSerializer

# ---------------------------------------------------------------------------
# Perfil de Barbero. Listado y detalle son públicos: el cliente necesita verlos para elegir
# barbero en el flujo de reserva antes incluso de loguearse.
# ---------------------------------------------------------------------------


class BarberoListView(generics.ListAPIView):
    """GET /api/barberos/ — listado público de barberos activos."""
    permission_classes = (AllowAny,)
    serializer_class = BarberoPublicSerializer
    queryset = Barbero.objects.filter(activo=True).select_related('usuario')


class BarberoDetailView(generics.RetrieveAPIView):
    """GET /api/barberos/<id>/ — detalle público, con horarios y servicios
    ofrecidos activos (para armar la pantalla de reserva)."""
    permission_classes = (AllowAny,)
    serializer_class = BarberoDetailSerializer
    queryset = Barbero.objects.filter(activo=True).select_related('usuario')


class BarberoMeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/barberos/me/ — el barbero autenticado ve y edita su
    propio perfil. El objeto sale siempre de request.user, nunca de la URL."""
    permission_classes = (IsAuthenticated,)
    serializer_class = BarberoMeSerializer
    http_method_names = ['get', 'patch']

    def get_object(self):
        barbero = getattr(self.request.user, 'barbero', None)
        if barbero is None:
            raise NotFound('Tu usuario no tiene un perfil de Barbero asociado.')
        return barbero
