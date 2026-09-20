from rest_framework import serializers

from ..models import Cliente
from .auth import UsuarioMeSerializer


class ClienteMeSerializer(serializers.ModelSerializer):
    """GET/PATCH /api/clientes/me/ — perfil propio del cliente autenticado.
    `telefono` vive en `Usuario`, no en `Cliente`, así que se expone acá con
    `source` punteado y se resuelve manualmente en `update()`."""

    usuario = UsuarioMeSerializer(read_only=True)
    telefono = serializers.CharField(source='usuario.telefono', required=False, allow_blank=True)

    class Meta:
        model = Cliente
        fields = ('id', 'fecha_nacimiento', 'fecha_registro', 'activo', 'telefono', 'usuario')
        read_only_fields = ('fecha_registro', 'activo')

    def update(self, instance, validated_data):
        usuario_data = validated_data.pop('usuario', None)
        if usuario_data and 'telefono' in usuario_data:
            instance.usuario.telefono = usuario_data['telefono']
            instance.usuario.save(update_fields=['telefono'])
        return super().update(instance, validated_data)
