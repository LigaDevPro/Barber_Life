from datetime import datetime, timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from ..models import Turno, Barbero, BarberoServicio


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
        return obj.puede_cancelar_cliente()


class TurnoCreateSerializer(serializers.ModelSerializer):
    """POST /api/turnos/ — reserva hecha por el cliente. `cliente` sale de
    request.user, nunca del body (ownership). `hora_fin` se calcula acá
    desde `servicio.duracion_minutos`, no la manda el frontend."""

    class Meta:
        model = Turno
        fields = ('id', 'barbero', 'servicio', 'fecha_turno', 'hora_inicio', 'observaciones')
        read_only_fields = ('id',)

    def validate(self, attrs):
        request = self.context['request']
        if getattr(request.user, 'cliente', None) is None:
            raise serializers.ValidationError(
                {'detail': 'Tu usuario no tiene un perfil de Cliente asociado; no se puede reservar.'}
            )

        barbero = attrs['barbero']
        servicio = attrs['servicio']
        fecha_turno = attrs['fecha_turno']
        hora_inicio = attrs['hora_inicio']

        if not barbero.activo:
            raise serializers.ValidationError({'barbero': 'Este barbero no está disponible actualmente.'})
        if not servicio.activo:
            raise serializers.ValidationError({'servicio': 'Este servicio no está disponible actualmente.'})

        inicio_dt = datetime.combine(fecha_turno, hora_inicio)
        fin_dt = inicio_dt + timedelta(minutes=servicio.duracion_minutos)
        if fin_dt.date() != inicio_dt.date():
            raise serializers.ValidationError(
                {'hora_inicio': 'El turno terminaría después de medianoche; elegí un horario más temprano.'}
            )
        hora_fin = fin_dt.time()

        inicio_aware = timezone.make_aware(inicio_dt) if timezone.is_naive(inicio_dt) else inicio_dt
        if inicio_aware < timezone.now():
            raise serializers.ValidationError({'fecha_turno': 'No se puede reservar un turno en el pasado.'})

        # BarberoServicio ata barbero+servicio+horario a propósito (ver
        # models.py): esta única consulta confirma que el barbero ofrece
        # este servicio, en un horario activo, ese día de la semana, y que
        # el rango pedido entra dentro de ese horario laboral.
        dia_semana = fecha_turno.isoweekday()
        ofrecido = BarberoServicio.objects.filter(
            barbero=barbero, servicio=servicio, activo=True,
            horario__activo=True, horario__dia_semana=dia_semana,
            horario__hora_inicio__lte=hora_inicio, horario__hora_fin__gte=hora_fin,
        ).exists()
        if not ofrecido:
            raise serializers.ValidationError(
                {'servicio': 'Este barbero no ofrece este servicio en ese horario.'}
            )

        attrs['_hora_fin'] = hora_fin
        return attrs

    def create(self, validated_data):
        hora_fin = validated_data.pop('_hora_fin')
        cliente = self.context['request'].user.cliente
        turno = Turno(cliente=cliente, hora_fin=hora_fin, **validated_data)

        with transaction.atomic():
            # Bloquea la fila del Barbero (no la de Turno: si es la primera
            # reserva del día para ese barbero, todavía no hay ningún Turno
            # que bloquear, y sin nada que lockear el lock no sirve de nada).
            # Esto serializa las creaciones concurrentes para el mismo
            # barbero, cerrando la ventana TOCTOU del check-then-save.
            Barbero.objects.select_for_update().get(pk=turno.barbero_id)
            try:
                turno.clean()
            except DjangoValidationError as e:
                raise serializers.ValidationError({'detail': e.messages[0]})
            turno.save()
        return turno


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
