"""
Emails transaccionales de Barber Life.

Escenarios:
  1. Bienvenida al registrarse                    -> usuario nuevo
  2. Reserva de turno registrada                  -> cliente
  3. Cambio de estado del turno (barbero/admin)   -> cliente
  4. Turno cancelado por el cliente               -> barbero

El envío es "best effort": si el servidor SMTP está caído o mal configurado
se loguea el error pero la operación de negocio (registro, reserva, etc.)
NO falla. Los datos de SMTP salen de variables de entorno (ver settings.py).
"""
import logging
from html import escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def _html(titulo, lineas, boton=None):
    """Plantilla HTML mínima (estilos inline, compatible con clientes de mail)."""
    parrafos = ''.join(f'<p style="margin:0 0 10px">{escape(linea)}</p>' for linea in lineas)
    cta = ''
    if boton:
        texto, url = boton
        cta = (
            f'<p style="margin:18px 0 0"><a href="{escape(url)}" style="background:#111;color:#fff;'
            f'padding:10px 18px;border-radius:6px;text-decoration:none">{escape(texto)}</a></p>'
        )
    return (
        '<div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;color:#111">'
        f'<h2 style="margin:0 0 14px">{escape(titulo)}</h2>{parrafos}{cta}'
        '<p style="margin:22px 0 0;color:#777;font-size:12px">Barber Life</p></div>'
    )


def _enviar(destinatario, asunto, titulo, lineas, boton=None):
    """Envía un mail multipart (texto + HTML). Devuelve True si salió."""
    if not destinatario:
        return False
    texto = '\n'.join(lineas)
    if boton:
        texto += f'\n\n{boton[0]}: {boton[1]}'
    try:
        mensaje = EmailMultiAlternatives(
            subject=asunto, body=texto, from_email=settings.DEFAULT_FROM_EMAIL, to=[destinatario],
        )
        mensaje.attach_alternative(_html(titulo, lineas, boton), 'text/html')
        mensaje.send()
        return True
    except Exception:  # noqa: BLE001 - un mail caído no debe romper la API
        logger.exception('No se pudo enviar el email "%s" a %s', asunto, destinatario)
        return False


def _detalle_turno(turno):
    return [
        f'Servicio: {turno.servicio.nombre}',
        f'Barbero: {turno.barbero.usuario.get_display_name()}',
        f'Fecha: {turno.fecha_turno:%d/%m/%Y}',
        f'Hora: {turno.hora_inicio:%H:%M}',
    ]


def enviar_bienvenida(usuario):
    nombre = usuario.get_display_name()
    return _enviar(
        usuario.email, 'Bienvenido a Barber Life', f'¡Hola, {nombre}!',
        ['Tu cuenta se creó correctamente.', 'Ya podés iniciar sesión y reservar tu primer turno.'],
        ('Ir a Barber Life', settings.FRONTEND_URL),
    )


def enviar_turno_reservado(turno):
    cliente = turno.cliente.usuario
    return _enviar(
        cliente.email, 'Reservaste un turno en Barber Life', 'Tu turno quedó reservado',
        [f'Hola {cliente.get_display_name()}, registramos tu reserva:', *_detalle_turno(turno),
         'Te avisamos por mail cuando el barbero lo confirme.'],
        ('Ver mis turnos', f'{settings.FRONTEND_URL}/mis-turnos'),
    )


def enviar_estado_turno(turno):
    cliente = turno.cliente.usuario
    estado = turno.get_estado_display()
    return _enviar(
        cliente.email, f'Tu turno ahora está {estado}', f'Tu turno está {estado}',
        [f'Hola {cliente.get_display_name()}, el estado de tu turno cambió a «{estado}».',
         *_detalle_turno(turno)],
        ('Ver mis turnos', f'{settings.FRONTEND_URL}/mis-turnos'),
    )


def enviar_turno_cancelado_al_barbero(turno):
    barbero = turno.barbero.usuario
    return _enviar(
        barbero.email, 'Un cliente canceló su turno', 'Turno cancelado',
        [f'Hola {barbero.get_display_name()}, {turno.cliente.usuario.get_display_name()} canceló su turno:',
         *_detalle_turno(turno)],
        ('Ver agenda', f'{settings.FRONTEND_URL}/turnos'),
    )
