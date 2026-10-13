"""
Integración con Mercado Pago (Checkout Pro) — CU-06. Encapsula el uso del
SDK oficial para no acoplar las vistas a los nombres de campos de la
librería ni a sus excepciones.
"""
import mercadopago
from django.conf import settings


class MercadoPagoError(Exception):
    """Error al hablar con la API de Mercado Pago: credenciales inválidas,
    timeout, o una respuesta que no es la esperada."""


def _sdk():
    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        raise MercadoPagoError('MERCADOPAGO_ACCESS_TOKEN no está configurado.')
    return mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)


def crear_preferencia(turno):
    """Crea la preferencia de pago (Checkout Pro) para un turno y devuelve
    el dict de respuesta de Mercado Pago (trae 'id' e 'init_point')."""
    preference_data = {
        'items': [{
            'title': f'{turno.servicio.nombre} - Barber Life',
            'quantity': 1,
            'unit_price': float(turno.precio()),
        }],
        'external_reference': str(turno.id),
    }
    try:
        result = _sdk().preference().create(preference_data)
    except Exception as e:
        raise MercadoPagoError(str(e)) from e

    if result.get('status') not in (200, 201):
        raise MercadoPagoError(f"Mercado Pago respondió {result.get('status')}: {result.get('response')}")
    return result['response']


def obtener_pago(payment_id):
    """Consulta el estado real de un pago por su id (el que llega en el
    webhook) — no hay que confiar ciegamente en el payload del POST."""
    try:
        result = _sdk().payment().get(payment_id)
    except Exception as e:
        raise MercadoPagoError(str(e)) from e

    if result.get('status') != 200:
        raise MercadoPagoError(f"Mercado Pago respondió {result.get('status')}: {result.get('response')}")
    return result['response']
