"""
Django settings — proyecto `core`, Barber Life.
Generado con `django-admin startproject core .` y completado para Sprint 2
(REST Framework, JWT, CORS, Postgres, Mongo, RBAC).
"""
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def env_list(key, default=''):
    raw = os.environ.get(key, default)
    return [item.strip() for item in raw.split(',') if item.strip()]


def env_bool(key, default=True):
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


DEBUG = env_bool('DEBUG', False)

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'dev-only-insecure-key'
    else:
        raise ImproperlyConfigured(
            'Falta DJANGO_SECRET_KEY. Copiá backend/.env.example a backend/.env '
            'o definí la variable de entorno.'
        )

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1,backend')

INSTALLED_APPS = [
    # daphne va primero: reemplaza a runserver por uno ASGI que además atiende WebSockets.
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'gestion',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Sirve los estáticos (admin, DRF) sin nginx; va justo después de SecurityMiddleware.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # RBAC: valida el JWT en cada request a /api/ (ver gestion/middleware.py).
    # El chequeo fino de rol por-endpoint vive en gestion/permissions.py.
    'gestion.middleware.RoleCheckMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# WebSockets (Django Channels). La capa en memoria alcanza con un solo proceso
# (runserver/daphne de la entrega); con varios procesos habría que usar Redis.
CHANNEL_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'barberlife'),
        'USER': os.environ.get('POSTGRES_USER', 'barberlife'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'barberlife' if DEBUG else ''),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

AUTH_USER_MODEL = 'gestion.Usuario'

# Con el ModelBackend por defecto, authenticate() devuelve None para un
# usuario inactivo y el login no puede distinguirlo de una contraseña
# incorrecta. AllowAllUsersModelBackend deja pasar a los inactivos: el
# LoginSerializer los rechaza después, y solo con la contraseña correcta, con
# el mensaje 'La cuenta está inactiva.'. La API sigue cerrada para ellos
# porque JWTAuthentication revisa is_active en cada request.
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.AllowAllUsersModelBackend']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Cordoba'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
# Destino de `collectstatic` (lo corre el Dockerfile al construir la imagen).
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

# Archivos subidos por usuarios (fotos de perfil). En Docker montar MEDIA_ROOT
# en un volumen para que sobrevivan a un rebuild del contenedor.
MEDIA_URL = '/media/'
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', str(BASE_DIR / 'media'))
FOTO_PERFIL_MAX_BYTES = int(os.environ.get('FOTO_PERFIL_MAX_BYTES', str(2 * 1024 * 1024)))
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 7,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOWED_ORIGINS = env_list(
    'CORS_ALLOWED_ORIGINS', 'http://localhost:4200,http://127.0.0.1:4200'
)
CORS_ALLOW_CREDENTIALS = True

# Detrás del proxy HTTPS de la plataforma (Railway, Render...): Django ve HTTP plano
# y necesita confiar en X-Forwarded-Proto para saber que la request original era HTTPS.
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', '')
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', False)

# MongoDB (colecciones no relacionales: notificaciones, eventos_log, analytics_cache)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'barberlife_nosql')

# Ventana de cancelación autónoma del cliente (RBAC - restricciones críticas, wiki)
CANCELACION_LIMITE_HORAS = int(os.environ.get('CANCELACION_LIMITE_HORAS', '2'))

# Mercado Pago (ya lo tenés instalado — clave lista para Sprint 3, CU-06;
# todavía no hay ninguna vista que la use en este sprint)
MERCADOPAGO_ACCESS_TOKEN = os.environ.get('MERCADOPAGO_ACCESS_TOKEN', '')

# URL base del frontend: a donde Mercado Pago devuelve al usuario al terminar el pago
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:4200')

# URL publica del backend, para que Mercado Pago llame al webhook (/api/pagos/webhook/).
# En desarrollo hay que exponerla con un tunel (ngrok, cloudflared). Si queda vacia, no se envia notification_url.
BACKEND_PUBLIC_URL = os.environ.get('BACKEND_PUBLIC_URL', '')

# Login con Google (OAuth 2.0 / OpenID Connect). Es el "Client ID" de una credencial
# "ID de cliente de OAuth > Aplicación web" de Google Cloud Console. No es un secreto,
# pero sin él el endpoint /api/auth/google/ responde 503.
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')

# Email (SMTP real o Mailtrap/Mailpit en desarrollo). Sin EMAIL_HOST en modo DEBUG
# los mails se imprimen en la consola del backend (docker compose logs backend).
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend' if EMAIL_HOST else (
        'django.core.mail.backends.console.EmailBackend' if DEBUG
        else 'django.core.mail.backends.smtp.EmailBackend'
    ),
)
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '10'))
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Barber Life <no-reply@barberlife.local>')
