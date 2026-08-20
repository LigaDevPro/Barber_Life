from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Usuario, Cliente, Barbero, Servicio, Turno


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Turnos / Gestión de turnos
# ---------------------------------------------------------------------------

class TurnoListSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.SerializerMethodField()
    servicio_nombre = serializers.CharField(source='servicio.nombre')
    hora = serializers.SerializerMethodField()
    fecha = serializers.SerializerMethodField()
    precio_total = serializers.SerializerMethodField()
    puede_cancelar = serializers.SerializerMethodField()

    class Meta:
        model = Turno
        fields = (
            'id', 'cliente_nombre', 'servicio_nombre', 'hora', 'fecha',
            'estado', 'precio_total', 'observaciones', 'puede_cancelar',
        )

    def get_cliente_nombre(self, obj):
        u = obj.cliente.usuario
        return u.get_full_name() or u.email.split('@')[0]

    def get_hora(self, obj):
        return obj.hora_inicio.strftime('%H:%M')

    def get_fecha(self, obj):
        return obj.fecha_turno.strftime('%d/%m/%Y')

    def get_precio_total(self, obj):
        # El DER no guarda precio_total en Turno; se calcula desde el precio
        # vigente del Servicio (o el personalizado en BarberoServicio).
        return obj.precio()

    def get_puede_cancelar(self, obj):
        return obj.estado in (Turno.Estado.PENDIENTE, Turno.Estado.CONFIRMADO) and obj.puede_cancelar_cliente()


class TurnoUpdateEstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turno
        fields = ('estado',)

    def validate_estado(self, value):
        if value not in Turno.Estado.values:
            raise serializers.ValidationError('Estado inválido.')
        return value


class ServicioMasSolicitadoSerializer(serializers.Serializer):
    servicio_id = serializers.IntegerField()
    nombre = serializers.CharField()
    precio = serializers.DecimalField(max_digits=10, decimal_places=2)
    cantidad = serializers.IntegerField()
