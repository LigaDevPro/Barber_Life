"""
ASGI config for core project.

Atiende dos protocolos:
  * http      -> la API REST de Django de siempre.
  * websocket -> /ws/notificaciones/ (notificaciones en tiempo real, ver gestion/consumers.py).

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Se inicializa Django antes de importar nada que toque los modelos.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import OriginValidator  # noqa: E402
from django.conf import settings  # noqa: E402

from gestion.routing import websocket_urlpatterns  # noqa: E402

# Orígenes que pueden abrir el socket: los hosts del backend y los del frontend
# (CORS_ALLOWED_ORIGINS). En producción el front vive en otro dominio (Vercel),
# así que validar solo contra ALLOWED_HOSTS rechazaría al propio frontend.
ORIGENES_WEBSOCKET = [*settings.ALLOWED_HOSTS, *settings.CORS_ALLOWED_ORIGINS]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    # Cualquier otro Origin se rechaza (evita que otra web abra el socket).
    'websocket': OriginValidator(URLRouter(websocket_urlpatterns), ORIGENES_WEBSOCKET),
})
