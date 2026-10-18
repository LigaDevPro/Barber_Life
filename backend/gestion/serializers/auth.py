from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
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


class LoginSerializer(serializers.Serializer):
    MENSAJE_CREDENCIALES = 'Email o contraseña incorrectos.'
    MENSAJE_CUENTA_INACTIVA = 'La cuenta está inactiva.'

    email = serializers.CharField(max_length=254)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs['email'].strip()
        candidato = Usuario.objects.filter(email__iexact=email).first()
        usuario = authenticate(
            username=candidato.username if candidato else email,
            password=attrs['password'],
        )
        if usuario is None:
            raise serializers.ValidationError(self.MENSAJE_CREDENCIALES)
        # Va DESPUÉS de authenticate(): el mensaje de cuenta inactiva solo se
        # muestra si la contraseña es correcta, así no sirve para averiguar
        # si un email existe.
        if not usuario.is_active:
            raise serializers.ValidationError(self.MENSAJE_CUENTA_INACTIVA)
        attrs['usuario'] = usuario
        return attrs

    def tokens(self):
        return tokens_para(self.validated_data['usuario'])


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
