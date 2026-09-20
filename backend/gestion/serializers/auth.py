from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import Usuario, Cliente


class RegisterSerializer(serializers.Serializer):
    """Registro público. Coincide con el wireframe de Register: email + password
    + confirmación. El rol se asigna 'cliente' por defecto — cuentas de
    barbero/administrador las da de alta el Administrador (CU-02, panel /admin/),
    igual que en un sistema real donde el staff no se autoregistra."""
    email = serializers.EmailField()
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
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        usuario = authenticate(username=attrs['email'], password=attrs['password'])
        if usuario is None:
            raise serializers.ValidationError('Email o contraseña incorrectos.')
        if not usuario.is_active:
            raise serializers.ValidationError('La cuenta está inactiva.')
        attrs['usuario'] = usuario
        return attrs

    def tokens(self):
        usuario = self.validated_data['usuario']
        refresh = RefreshToken.for_user(usuario)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'usuario': UsuarioMeSerializer(usuario).data,
        }


class UsuarioMeSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ('id', 'nombre', 'email', 'rol', 'estado', 'telefono')

    def get_nombre(self, obj):
        return obj.get_full_name() or obj.email.split('@')[0]
