from rest_framework import serializers

from ..models import Pago, Turno


class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = (
            'id', 'turno', 'monto_total', 'metodo_pago', 'estado',
            'fecha_pago', 'transaccion_id', 'fecha_creacion',
        )
        read_only_fields = fields


class PagoCreateSerializer(serializers.Serializer):
    """POST /api/pagos/ — solo pide el turno; monto, preferencia de Mercado
    Pago y el resto los arma la vista."""
    turno = serializers.PrimaryKeyRelatedField(queryset=Turno.objects.all())

    def validate_turno(self, value):
        if value.estado != Turno.Estado.PENDIENTE:
            raise serializers.ValidationError('Solo se puede generar un pago para un turno pendiente.')
        if hasattr(value, 'pago'):
            raise serializers.ValidationError('Este turno ya tiene un pago asociado.')
        return value
