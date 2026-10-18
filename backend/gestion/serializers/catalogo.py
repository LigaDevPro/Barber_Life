from rest_framework import serializers

from ..models import Servicio, Horario, BarberoServicio


class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ('id', 'nombre', 'duracion_minutos', 'precio', 'activo')
        extra_kwargs = {
            'duracion_minutos': {'min_value': 1},
            'precio': {'min_value': 0},
        }


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
        extra_kwargs = {
            'barbero': {'required': False},
            'intervalo_minutos': {'min_value': 1},
        }

    def validate(self, attrs):
        # En un PATCH parcial puede venir solo uno de los dos extremos: el
        # otro se toma de la instancia, para no dejar pasar un rango inverso.
        instancia = self.instance
        hora_inicio = attrs.get('hora_inicio') or (instancia.hora_inicio if instancia else None)
        hora_fin = attrs.get('hora_fin') or (instancia.hora_fin if instancia else None)
        if hora_inicio is not None and hora_fin is not None and hora_fin <= hora_inicio:
            raise serializers.ValidationError(
                {'hora_fin': 'La hora de fin tiene que ser posterior a la hora de inicio.'}
            )
        return attrs


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
        extra_kwargs = {'precio_personalizado': {'min_value': 0}}
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