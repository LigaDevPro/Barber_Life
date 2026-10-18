from django.conf import settings
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import (
    RegisterSerializer, LoginSerializer, GoogleLoginSerializer, UsuarioMeSerializer, tokens_para,
)
from ..emails import enviar_bienvenida
from ..google_auth import CredencialGoogleInvalida, GoogleNoDisponible, verificar_credencial
from ..models import Usuario, Cliente
from ..mongo import registrar_notificacion, registrar_evento_log


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
        enviar_bienvenida(usuario)
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


class GoogleLoginView(APIView):
    """POST /api/auth/google/ — público. Login / registro con Google (OAuth 2.0 + OpenID Connect).

    Recibe el ID token de Google en `credential`, lo verifica y:
      * si ya hay una cuenta con ese correo (ya verificado por Google), inicia sesión en ella;
      * si no, crea una cuenta de Cliente sin contraseña (el rol nunca viene del request).
    Responde igual que el login: access + refresh + usuario."""
    permission_classes = (AllowAny,)

    def post(self, request):
        if not settings.GOOGLE_CLIENT_ID:
            return Response(
                {'detail': 'El acceso con Google no está configurado.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            datos = verificar_credencial(serializer.validated_data['credential'])
        except CredencialGoogleInvalida as error:
            raise serializers.ValidationError(str(error))
        except GoogleNoDisponible as error:
            return Response({'detail': str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        usuario = Usuario.objects.filter(email__iexact=datos['email']).first()
        if usuario is None:
            usuario = self._crear_cliente(datos)
            accion = 'registro_google'
        else:
            if not usuario.is_active:
                raise serializers.ValidationError('La cuenta está inactiva.')
            accion = 'login_google'
        registrar_evento_log(usuario.id, accion, {'email': usuario.email})
        return Response(tokens_para(usuario), status=status.HTTP_200_OK)

    @staticmethod
    def _crear_cliente(datos):
        email = datos['email'].strip()
        usuario = Usuario.objects.create_user(
            username=email,
            email=email,
            password=None,  # contraseña inutilizable: solo entra con Google
            rol=Usuario.Rol.CLIENTE,
            first_name=(datos.get('given_name') or '')[:150],
            last_name=(datos.get('family_name') or '')[:150],
        )
        Cliente.objects.create(usuario=usuario)
        registrar_notificacion(usuario.id, 'bienvenida', 'Bienvenido a Barber Life')
        enviar_bienvenida(usuario)
        return usuario


class MeView(APIView):
    """GET /api/auth/me/ — el frontend lo usa para saber el rol del usuario
    logueado y decidir a qué rutas puede navegar (authGuard + roleGuard)."""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(UsuarioMeSerializer(request.user).data)
