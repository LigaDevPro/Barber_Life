from rest_framework import serializers

from ..models import Resena, Turno


class ResenaSerializer(serializers.ModelSerializer):
    """GET /api/resenas/?barbero=<id> — público."""
    cliente_nombre = serializers.SerializerMethodField()
    fecha = serializers.DateTimeField(source='fecha_creacion', read_only=True)

    class Meta:
        model = Resena
        fields = ('id', 'puntaje', 'comentario', 'fecha', 'cliente_nombre', 'barbero')

    def get_cliente_nombre(self, obj):
        return obj.cliente.usuario.get_display_name()


class ResenaCreateSerializer(serializers.ModelSerializer):
    """POST /api/resenas/ — el cliente califica un turno ya completado."""

    class Meta:
        model = Resena
        fields = ('id', 'turno', 'puntaje', 'comentario')

    def validate_turno(self, value):
        if value.estado != Turno.Estado.COMPLETADO:
            raise serializers.ValidationError('Solo se puede reseñar un turno completado.')
        if hasattr(value, 'resena'):
            raise serializers.ValidationError('Este turno ya tiene una reseña.')
        return value
