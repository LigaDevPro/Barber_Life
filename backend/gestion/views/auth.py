from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import RegisterSerializer, LoginSerializer, UsuarioMeSerializer
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


class MeView(APIView):
    """GET /api/auth/me/ — el frontend lo usa para saber el rol del usuario
    logueado y decidir a qué rutas puede navegar (authGuard + roleGuard)."""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(UsuarioMeSerializer(request.user).data)
