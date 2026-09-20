from rest_framework import serializers

from ..models import Turno


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
        return obj.cliente.usuario.get_display_name()

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
