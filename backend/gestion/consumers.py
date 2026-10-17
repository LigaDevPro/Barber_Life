"""
WebSocket de notificaciones en tiempo real:  ws://<host>/ws/notificaciones/

Protocolo (JSON):
  cliente -> {"type": "auth", "token": "<access JWT>"}   (obligatorio, primer mensaje)
  servidor-> {"type": "auth_ok"}                         o  {"type": "auth_error"} y cierra (4401)
  servidor-> {"type": "notificacion", "data": {...}}     por cada notificación nueva del usuario
  cliente -> {"type": "ping"}  /  servidor -> {"type": "pong"}

El token viaja en el primer mensaje y no en la URL, así no queda en logs ni historial.
Si en AUTH_TIMEOUT segundos no llega una autenticación válida, se cierra la conexión.
"""
import asyncio

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from .models import Usuario
from .realtime import grupo_de_usuario

CIERRE_NO_AUTORIZADO = 4401


@database_sync_to_async
def _usuario_activo_id(token):
    """Devuelve el id del usuario dueño de un access token válido, o None."""
    try:
        validado = AccessToken(token)
    except (TokenError, TypeError):
        return None
    usuario_id = validado.get('user_id')
    if usuario_id is None or not Usuario.objects.filter(pk=usuario_id, is_active=True).exists():
        return None
    return usuario_id


class NotificacionesConsumer(AsyncJsonWebsocketConsumer):
    AUTH_TIMEOUT = 10  # segundos

    async def connect(self):
        self.usuario_id = None
        self.grupo = None
        await self.accept()
        self._vencimiento = asyncio.create_task(self._cerrar_si_no_se_autentica())

    async def _cerrar_si_no_se_autentica(self):
        await asyncio.sleep(self.AUTH_TIMEOUT)
        if self.usuario_id is None:
            await self.close(code=CIERRE_NO_AUTORIZADO)

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict):
            return
        if self.usuario_id is None:
            await self._autenticar(content)
        elif content.get('type') == 'ping':
            await self.send_json({'type': 'pong'})

    async def _autenticar(self, content):
        token = content.get('token') if content.get('type') == 'auth' else None
        usuario_id = await _usuario_activo_id(token) if isinstance(token, str) else None
        if usuario_id is None:
            await self.send_json({'type': 'auth_error'})
            await self.close(code=CIERRE_NO_AUTORIZADO)
            return
        self.usuario_id = usuario_id
        self.grupo = grupo_de_usuario(usuario_id)
        await self.channel_layer.group_add(self.grupo, self.channel_name)
        await self.send_json({'type': 'auth_ok'})

    async def disconnect(self, code):
        vencimiento = getattr(self, '_vencimiento', None)
        if vencimiento:
            vencimiento.cancel()
        if getattr(self, 'grupo', None):
            await self.channel_layer.group_discard(self.grupo, self.channel_name)

    async def notificacion(self, evento):
        """Handler del mensaje de grupo {'type': 'notificacion'} (ver realtime.py)."""
        await self.send_json({'type': 'notificacion', 'data': evento['data']})
