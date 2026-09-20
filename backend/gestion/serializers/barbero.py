from rest_framework import serializers

from ..models import Barbero, Horario, BarberoServicio
from .auth import UsuarioMeSerializer


class HorarioInlineSerializer(serializers.ModelSerializer):
    """Representación liviana de un horario, embebida en el perfil público
    de un barbero. Si más adelante se agrega un CRUD completo de Horario con
    su propio serializer, conviene unificar y que éste lo reutilice en vez
    de duplicarlo."""

    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)

    class Meta:
        model = Horario
        fields = ('id', 'dia_semana', 'dia_semana_display', 'hora_inicio', 'hora_fin', 'intervalo_minutos')


class ServicioOfrecidoInlineSerializer(serializers.ModelSerializer):
    """Idem HorarioInlineSerializer: versión liviana para el perfil público."""

    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)
    precio = serializers.SerializerMethodField()

    class Meta:
        model = BarberoServicio
        fields = ('id', 'servicio', 'servicio_nombre', 'precio', 'horario')

    def get_precio(self, obj):
        return obj.precio_final()


class BarberoPublicSerializer(serializers.ModelSerializer):
    """GET /api/barberos/ — listado público, solo lo necesario para elegir
    barbero en el flujo de reserva."""

    nombre = serializers.SerializerMethodField()

    class Meta:
        model = Barbero
        fields = ('id', 'nombre', 'foto_perfil_url', 'activo')

    def get_nombre(self, obj):
        u = obj.usuario
        return u.get_full_name() or u.email.split('@')[0]


class BarberoDetailSerializer(BarberoPublicSerializer):
    """GET /api/barberos/<id>/ — detalle público: suma horarios y servicios
    ofrecidos activos, para la pantalla de reserva (elegir servicio + horario)."""

    horarios = serializers.SerializerMethodField()
    servicios_ofrecidos = serializers.SerializerMethodField()

    class Meta(BarberoPublicSerializer.Meta):
        fields = BarberoPublicSerializer.Meta.fields + ('horarios', 'servicios_ofrecidos')

    def get_horarios(self, obj):
        qs = obj.horarios.filter(activo=True)
        return HorarioInlineSerializer(qs, many=True).data

    def get_servicios_ofrecidos(self, obj):
        qs = obj.servicios_ofrecidos.filter(activo=True)
        return ServicioOfrecidoInlineSerializer(qs, many=True).data


class BarberoMeSerializer(serializers.ModelSerializer):
    """GET/PATCH /api/barberos/me/ — perfil propio del barbero autenticado."""

    usuario = UsuarioMeSerializer(read_only=True)

    class Meta:
        model = Barbero
        fields = ('id', 'foto_perfil_url', 'activo', 'fecha_creacion', 'usuario')
        read_only_fields = ('activo', 'fecha_creacion')
