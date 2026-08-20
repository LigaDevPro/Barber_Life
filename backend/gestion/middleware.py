"""
RoleCheckMiddleware

Implementa el primer escalón del diagrama de seguridad de la wiki
(ESTRUCTURA-Y-ARQUITECTURA > Implementación de Seguridad):

    [ Petición HTTP ]
            v
    JWT Middleware          -> Token inválido/ausente en ruta protegida -> 401
            v Token válido
    Role Check Middleware   -> (delegado a permission_classes por vista, ver gestion/permissions.py)
            v Autorizado
    [ Ejecuta Vista ]

Esta clase valida que exista un JWT válido para cualquier ruta bajo /api/
que no sea pública (registro/login/refresh/admin), y deja el chequeo fino de
rol por-endpoint a los DRF permission_classes, que sí conocen la semántica de
cada vista (por ejemplo "barbero ve su propia agenda, no la ajena").
Antes esto no estaba conectado; ahora corre en cada request real.
"""
import jwt as pyjwt
from django.conf import settings
from django.http import JsonResponse

RUTAS_PUBLICAS = (
    '/api/auth/register/',
    '/api/auth/login/',
    '/api/auth/refresh/',
    '/admin/',
)


class RoleCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if not path.startswith('/api/') or path.startswith(RUTAS_PUBLICAS):
            return self.get_response(request)

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse(
                {'detail': 'No se proporcionó un token de autenticación válido.'},
                status=401,
            )

        token = auth_header.split(' ', 1)[1]
        try:
            # Simple JWT firma con la SECRET_KEY del proyecto por default (HS256).
            pyjwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except pyjwt.ExpiredSignatureError:
            return JsonResponse({'detail': 'El token expiró.'}, status=401)
        except pyjwt.InvalidTokenError:
            return JsonResponse({'detail': 'Token inválido.'}, status=401)

        # Token válido -> sigue a la vista, donde DRF (JWTAuthentication +
        # permission_classes de gestion/permissions.py) resuelve request.user
        # y aplica el 403 específico según el rol y el recurso solicitado.
        return self.get_response(request)
