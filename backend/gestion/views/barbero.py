import uuid

from django.conf import settings
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from ..permissions import EsBarbero
from .mixins import PerfilPropioMixin
from ..models import Barbero
from ..mongo import registrar_evento_log
from ..serializers import (
    BarberoPublicSerializer, BarberoDetailSerializer, BarberoMeSerializer, FotoPerfilSerializer,
)

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
    permission_classes = (EsBarbero,)
    serializer_class = BarberoMeSerializer
    http_method_names = ['get', 'patch']
    perfil_attr = 'barbero'
    perfil_no_encontrado_mensaje = 'Tu usuario no tiene un perfil de Barbero asociado.'


class BarberoFotoView(APIView):
    """POST /api/barberos/me/foto/ — el barbero sube su foto de perfil
    (multipart, campo `foto`). Reemplaza la anterior y borra el archivo viejo.
    DELETE /api/barberos/me/foto/ — la quita. Ambos devuelven el perfil propio."""
    permission_classes = (EsBarbero,)
    parser_classes = (MultiPartParser,)

    def _barbero(self, request):
        barbero = getattr(request.user, 'barbero', None)
        if barbero is None:
            raise NotFound('Tu usuario no tiene un perfil de Barbero asociado.')
        return barbero

    def _url_publica(self, request, barbero):
        base = settings.BACKEND_PUBLIC_URL.rstrip('/')
        return f'{base}{barbero.foto_perfil.url}' if base else request.build_absolute_uri(barbero.foto_perfil.url)

    def post(self, request):
        barbero = self._barbero(request)
        serializer = FotoPerfilSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        archivo = serializer.validated_data['foto']
        extension = FotoPerfilSerializer.FORMATOS[archivo.image.format]
        archivo.name = f'{uuid.uuid4().hex}.{extension}'  # nombre propio: nunca confiamos en el del cliente

        if barbero.foto_perfil:
            barbero.foto_perfil.delete(save=False)
        barbero.foto_perfil = archivo
        barbero.save(update_fields=['foto_perfil'])
        barbero.foto_perfil_url = self._url_publica(request, barbero)
        barbero.save(update_fields=['foto_perfil_url'])
        registrar_evento_log(request.user.id, 'subida_foto_perfil', {'barbero_id': barbero.id})
        return Response(BarberoMeSerializer(barbero).data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        barbero = self._barbero(request)
        if barbero.foto_perfil:
            barbero.foto_perfil.delete(save=False)
        barbero.foto_perfil = ''
        barbero.foto_perfil_url = ''
        barbero.save(update_fields=['foto_perfil', 'foto_perfil_url'])
        registrar_evento_log(request.user.id, 'baja_foto_perfil', {'barbero_id': barbero.id})
        return Response(BarberoMeSerializer(barbero).data)
