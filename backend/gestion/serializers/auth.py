from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import Usuario, Cliente


def tokens_para(usuario):
    """Misma respuesta que el login con contraseña: access + refresh + datos del usuario."""
    refresh = RefreshToken.for_user(usuario)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'usuario': UsuarioMeSerializer(usuario).data,
    }


class RegisterSerializer(serializers.Serializer):
    """Registro público. Coincide con el wireframe de Register: email + password
    + confirmación. El rol se asigna 'cliente' por defecto — cuentas de
    barbero/administrador las da de alta el Administrador (CU-02, panel /admin/),
    igual que en un sistema real donde el staff no se autoregistra."""
    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Ya existe una cuenta con ese correo electrónico.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Las contraseñas no coinciden.'})
        return attrs

    def create(self, validated_data):
        email = validated_data['email']
        usuario = Usuario.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
            rol=Usuario.Rol.CLIENTE,
        )
        Cliente.objects.create(usuario=usuario)
        return usuario


def _clave_intentos(email):
    return f'login_fallidos:{email.strip().lower()}'


def limpiar_intentos_fallidos(email):
    cache.delete(_clave_intentos(email))


class LoginSerializer(serializers.Serializer):
    MENSAJE_CREDENCIALES = 'Email o contraseña incorrectos.'
    MENSAJE_CUENTA_INACTIVA = 'La cuenta está inactiva.'
    MENSAJE_BLOQUEO = (
        'Demasiados intentos fallidos. Esperá {minutos} minutos o recuperá tu contraseña '
        'desde «¿Olvidaste tu contraseña?».'
    )

    email = serializers.CharField(max_length=254)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs['email'].strip()
        clave = _clave_intentos(email)
        bloqueo = self.MENSAJE_BLOQUEO.format(minutos=settings.LOGIN_BLOQUEO_MINUTOS)
        # El contador va por email y no por usuario: un email inexistente se
        # bloquea igual, así el bloqueo no revela qué cuentas existen.
        # shortcut: la caché por defecto (LocMem) es por proceso; con varios
        # workers hay que usar una caché compartida (Redis o base de datos).
        if cache.get(clave, 0) >= settings.LOGIN_MAX_INTENTOS:
            raise serializers.ValidationError(bloqueo)

        candidato = Usuario.objects.filter(email__iexact=email).first()
        usuario = authenticate(
            username=candidato.username if candidato else email,
            password=attrs['password'],
        )
        if usuario is None:
            intentos = cache.get(clave, 0) + 1
            cache.set(clave, intentos, settings.LOGIN_BLOQUEO_MINUTOS * 60)
            if intentos >= settings.LOGIN_MAX_INTENTOS:
                raise serializers.ValidationError(bloqueo)
            raise serializers.ValidationError(self.MENSAJE_CREDENCIALES)
        cache.delete(clave)
        # Va DESPUÉS de authenticate(): el mensaje de cuenta inactiva solo se
        # muestra si la contraseña es correcta, así no sirve para averiguar
        # si un email existe.
        if not usuario.is_active:
            raise serializers.ValidationError(self.MENSAJE_CUENTA_INACTIVA)
        attrs['usuario'] = usuario
        return attrs

    def tokens(self):
        return tokens_para(self.validated_data['usuario'])


class RecuperarContrasenaSerializer(serializers.Serializer):
    """POST /api/auth/password-reset/ — pide el enlace de recuperación."""
    email = serializers.EmailField(max_length=254)


class RestablecerContrasenaSerializer(serializers.Serializer):
    """POST /api/auth/password-reset/confirm/ — `uid` y `token` vienen del enlace del mail."""
    MENSAJE_ENLACE_INVALIDO = 'El enlace no es válido o ya venció. Pedí uno nuevo.'

    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            pk = force_str(urlsafe_base64_decode(attrs['uid']))
            usuario = Usuario.objects.get(pk=pk, is_active=True)
        except (ValueError, TypeError, OverflowError, Usuario.DoesNotExist):
            raise serializers.ValidationError(self.MENSAJE_ENLACE_INVALIDO)
        # El token deja de servir cuando cambia la contraseña: es de un solo uso.
        if not default_token_generator.check_token(usuario, attrs['token']):
            raise serializers.ValidationError(self.MENSAJE_ENLACE_INVALIDO)
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Las contraseñas no coinciden.'})
        try:
            validate_password(attrs['password'], usuario)
        except DjangoValidationError as error:
            raise serializers.ValidationError({'password': list(error.messages)})
        attrs['usuario'] = usuario
        return attrs

    def save(self):
        usuario = self.validated_data['usuario']
        usuario.set_password(self.validated_data['password'])
        usuario.save(update_fields=['password'])
        limpiar_intentos_fallidos(usuario.email)
        return usuario


class GoogleLoginSerializer(serializers.Serializer):
    """POST /api/auth/google/ — `credential` es el ID token que entrega Google."""
    credential = serializers.CharField(max_length=4096)


class UsuarioMeSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ('id', 'nombre', 'email', 'rol', 'estado', 'telefono')

    def get_nombre(self, obj):
        return obj.get_display_name()
