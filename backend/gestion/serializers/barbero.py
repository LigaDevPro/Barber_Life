from django.conf import settings
from rest_framework import serializers

from ..models import Barbero, Horario, BarberoServicio
from .auth import UsuarioMeSerializer


class HorarioInlineSerializer(serializers.ModelSerializer):
    """Representación liviana de un horario, embebida en el perfil público
    de un barbero (sin `barbero` ni `activo`, que ya están implícitos en ese
    contexto). El CRUD completo vive en HorarioSerializer (serializers/catalogo.py)."""

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
        return obj.usuario.get_display_name()


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
        # horario__activo=True además de activo=True: si se desactiva un
        # horario sin tocar el BarberoServicio asociado, no queremos devolver
        # un servicio cuyo `horario` no aparece en la lista de `horarios` de
        # esta misma respuesta.
        qs = obj.servicios_ofrecidos.filter(activo=True, horario__activo=True).select_related('servicio')
        return ServicioOfrecidoInlineSerializer(qs, many=True).data


class BarberoMeSerializer(serializers.ModelSerializer):
    """GET/PATCH /api/barberos/me/ — perfil propio del barbero autenticado."""

    usuario = UsuarioMeSerializer(read_only=True)

    class Meta:
        model = Barbero
        fields = ('id', 'foto_perfil_url', 'activo', 'fecha_creacion', 'usuario')
        read_only_fields = ('activo', 'fecha_creacion')


class FotoPerfilSerializer(serializers.Serializer):
    """POST /api/barberos/me/foto/ (multipart/form-data, campo `foto`).
    Acepta solo JPEG, PNG o WebP reales (Pillow abre el archivo: no alcanza
    con la extensión ni con el Content-Type) y hasta FOTO_PERFIL_MAX_BYTES."""

    FORMATOS = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}

    foto = serializers.ImageField(
        error_messages={
            'invalid_image': 'El archivo no es una imagen válida (JPEG, PNG o WebP).',
            'required': 'Mandá la imagen en el campo "foto".',
            'empty': 'El archivo está vacío.',
        },
    )

    def validate_foto(self, archivo):
        formato = getattr(getattr(archivo, 'image', None), 'format', None)
        if formato not in self.FORMATOS:
            raise serializers.ValidationError('Formato no permitido. Usá JPEG, PNG o WebP.')
        maximo = settings.FOTO_PERFIL_MAX_BYTES
        if archivo.size > maximo:
            raise serializers.ValidationError(f'La imagen pesa más de {maximo // (1024 * 1024)} MB.')
        return archivo
