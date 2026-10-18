"""
Verificación de credenciales de "Iniciar sesión con Google" (Google Identity Services).

El frontend recibe de Google un ID token (JWT firmado) y lo manda a
POST /api/auth/google/. Acá se valida: firma con las claves públicas de Google,
vencimiento, emisor y que el token fue emitido para NUESTRA app (audience =
GOOGLE_CLIENT_ID). No hace falta ningún "client secret".
"""
from django.conf import settings
from google.auth import exceptions as google_exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


class CredencialGoogleInvalida(Exception):
    pass


class GoogleNoDisponible(Exception):
    """No se pudieron bajar las claves públicas de Google (sin internet / Google caído)."""


def verificar_credencial(credencial):
    """Devuelve los datos del usuario de Google o levanta CredencialGoogleInvalida."""
    try:
        datos = id_token.verify_oauth2_token(credencial, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
    except google_exceptions.TransportError as error:
        raise GoogleNoDisponible('No se pudo contactar a Google para validar la credencial.') from error
    except (ValueError, TypeError, google_exceptions.GoogleAuthError) as error:
        # token mal formado, firma, vencimiento, emisor o audience incorrectos
        raise CredencialGoogleInvalida('La credencial de Google no es válida.') from error
    if not datos.get('email') or datos.get('email_verified') is not True:
        raise CredencialGoogleInvalida('Tu cuenta de Google no tiene el correo verificado.')
    return datos
