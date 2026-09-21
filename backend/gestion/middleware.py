"""
RoleCheckMiddleware

Implementa el primer escalón del diagrama de seguridad del proyecto:

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
    # Ruta exacta (no un prefijo compartido con otros endpoints): la llama
    # Mercado Pago, no un usuario logueado.
    '/api/pagos/webhook/',
)

# Prefijos con lectura pública (catálogos/listados: barberos, servicios, la
# oferta barbero-servicio). Solo exime GET/HEAD — POST/PATCH/DELETE bajo
# estos mismos prefijos siguen exigiendo JWT acá, y el permiso fino
# (admin-only, dueño del recurso, etc.) lo resuelve cada vista con sus
# permission_classes.
PREFIJOS_LECTURA_PUBLICA = (
    '/api/barberos/',
    '/api/servicios/',
    '/api/barbero-servicio/',
    '/api/resenas/',
)


class RoleCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if not path.startswith('/api/'):
            return self.get_response(request)

        es_publica = path.startswith(RUTAS_PUBLICAS)
        # `/me/` es siempre privado (perfil propio) aunque comparta prefijo
        # con un catálogo público (p.ej. '/api/barberos/me/' vs
        # '/api/barberos/<id>/') — nunca lo tratamos como lectura pública acá,
        # sea cual sea PREFIJOS_LECTURA_PUBLICA.
        es_lectura_publica = (
            request.method in ('GET', 'HEAD')
            and path.startswith(PREFIJOS_LECTURA_PUBLICA)
            and not path.endswith('/me/')
        )
        if es_publica or es_lectura_publica:
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
