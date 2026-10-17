"""
Envío de eventos en tiempo real a los usuarios conectados por WebSocket.

Cada usuario autenticado se une al grupo `usuario_<id>` (ver consumers.py);
acá se publica en ese grupo. Es "best effort": si la capa de canales falla
no se rompe el flujo de negocio.
"""
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def grupo_de_usuario(usuario_id):
    return f'usuario_{usuario_id}'


def enviar_notificacion(usuario_id, notificacion):
    """Empuja una notificación (dict JSON-serializable) al usuario si está conectado."""
    try:
        capa = get_channel_layer()
        if capa is None:
            return
        async_to_sync(capa.group_send)(
            grupo_de_usuario(usuario_id),
            {'type': 'notificacion', 'data': notificacion},
        )
    except Exception:  # noqa: BLE001 - el tiempo real nunca debe romper la API
        logger.exception('No se pudo enviar la notificación en tiempo real al usuario %s', usuario_id)
