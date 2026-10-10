from rest_framework import serializers

from ..models import Servicio, Horario, BarberoServicio


class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ('id', 'nombre', 'duracion_minutos', 'precio', 'activo')


class HorarioSerializer(serializers.ModelSerializer):
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)

    class Meta:
        model = Horario
        fields = (
            'id', 'barbero', 'dia_semana', 'dia_semana_display',
            'hora_inicio', 'hora_fin', 'intervalo_minutos', 'activo',
        )
        # barbero no es required acá: cuando lo crea un barbero (no admin), la
        # vista lo inyecta en perform_create() desde request.user, no del body.
        extra_kwargs = {'barbero': {'required': False}}


class BarberoServicioSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)
    precio = serializers.SerializerMethodField()

    class Meta:
        model = BarberoServicio
        fields = (
            'id', 'barbero', 'servicio', 'servicio_nombre', 'horario',
            'precio_personalizado', 'precio', 'activo', 'fecha_creacion',
        )
        read_only_fields = ('fecha_creacion',)
        # OJO: `barbero` participa del unique_together del modelo, así que DRF
        # fuerza required=True acá sin importar extra_kwargs — por eso la vista
        # inyecta `barbero` en request.data antes de is_valid(), en vez de
        # confiar en required=False como hace HorarioSerializer.

    def get_precio(self, obj):
        return obj.precio_final()

    def validate(self, attrs):
        # Corre tanto en POST como en PATCH. Antes esta regla vivía solo en
        # BarberoServicioListCreateView.create(), y el PATCH del detalle
        # quedaba sin protección.
        instancia = self.instance

        if instancia is not None:
            nuevo_barbero = attrs.get('barbero')
            if nuevo_barbero is not None and nuevo_barbero.id != instancia.barbero_id:
                raise serializers.ValidationError(
                    {'barbero': 'No se puede reasignar una oferta a otro barbero.'}
                )

        barbero = attrs.get('barbero') or (instancia.barbero if instancia else None)
        horario = attrs.get('horario') or (instancia.horario if instancia else None)
        if barbero is not None and horario is not None and horario.barbero_id != barbero.id:
            raise serializers.ValidationError(
                {'horario': 'El horario no pertenece a este barbero.'}
            )
        return attrs