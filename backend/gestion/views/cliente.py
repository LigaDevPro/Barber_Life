from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated

from ..serializers import ClienteMeSerializer

# ---------------------------------------------------------------------------
# Perfil de Cliente.
# ---------------------------------------------------------------------------


class ClienteMeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/clientes/me/ — el cliente autenticado ve y edita su
    propio perfil (fecha_nacimiento, telefono). No expone ningún dato de
    otros clientes: el objeto sale siempre de request.user, nunca de la URL."""
    permission_classes = (IsAuthenticated,)
    serializer_class = ClienteMeSerializer
    http_method_names = ['get', 'patch']

    def get_object(self):
        cliente = getattr(self.request.user, 'cliente', None)
        if cliente is None:
            raise NotFound('Tu usuario no tiene un perfil de Cliente asociado.')
        return cliente
