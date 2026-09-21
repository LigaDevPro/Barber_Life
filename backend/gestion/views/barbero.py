from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from .mixins import PerfilPropioMixin
from ..models import Barbero
from ..serializers import BarberoPublicSerializer, BarberoDetailSerializer, BarberoMeSerializer

# ---------------------------------------------------------------------------
# Perfil de Barbero. Listado y detalle son públicos: el cliente necesita verlos para elegir
# barbero en el flujo de reserva antes incluso de loguearse.
# ---------------------------------------------------------------------------


class BarberoListView(generics.ListAPIView):
    """GET /api/barberos/ — listado público de barberos activos. Sin
    paginar a propósito: es la lista completa para elegir barbero en el
    flujo de reserva, no una tabla que necesite paginado."""
    permission_classes = (AllowAny,)
    serializer_class = BarberoPublicSerializer
    pagination_class = None
    queryset = Barbero.objects.filter(activo=True).select_related('usuario')


class BarberoDetailView(generics.RetrieveAPIView):
    """GET /api/barberos/<id>/ — detalle público, con horarios y servicios
    ofrecidos activos (para armar la pantalla de reserva)."""
    permission_classes = (AllowAny,)
    serializer_class = BarberoDetailSerializer
    queryset = Barbero.objects.filter(activo=True).select_related('usuario')


class BarberoMeView(PerfilPropioMixin, generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/barberos/me/ — el barbero autenticado ve y edita su
    propio perfil. El objeto sale siempre de request.user, nunca de la URL."""
    permission_classes = (IsAuthenticated,)
    serializer_class = BarberoMeSerializer
    http_method_names = ['get', 'patch']
    perfil_attr = 'barbero'
    perfil_no_encontrado_mensaje = 'Tu usuario no tiene un perfil de Barbero asociado.'
