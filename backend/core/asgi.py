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
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

from gestion.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    # Solo acepta conexiones cuyo Origin esté en ALLOWED_HOSTS (evita que otra web abra el socket).
    'websocket': AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns)),
})
