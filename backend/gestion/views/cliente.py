from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .mixins import PerfilPropioMixin
from ..serializers import ClienteMeSerializer

# ---------------------------------------------------------------------------
# Perfil de Cliente.
# ---------------------------------------------------------------------------


class ClienteMeView(PerfilPropioMixin, generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/clientes/me/ — el cliente autenticado ve y edita su
    propio perfil (fecha_nacimiento, telefono). No expone ningún dato de
    otros clientes: el objeto sale siempre de request.user, nunca de la URL."""
    permission_classes = (IsAuthenticated,)
    serializer_class = ClienteMeSerializer
    http_method_names = ['get', 'patch']
    perfil_attr = 'cliente'
    perfil_no_encontrado_mensaje = 'Tu usuario no tiene un perfil de Cliente asociado.'
