"""
Re-exporta todos los serializers para que el resto del código (views, etc.)
pueda seguir haciendo `from gestion.serializers import X` sin saber en qué
submódulo vive cada clase. Cada dominio (auth, turno, cliente, barbero, ...)
vive en su propio archivo para que distintas personas puedan trabajar en
paralelo sin pisarse en el mismo archivo.
"""
from .auth import RegisterSerializer, LoginSerializer, UsuarioMeSerializer
from .turno import TurnoListSerializer, TurnoUpdateEstadoSerializer, ServicioMasSolicitadoSerializer
from .cliente import ClienteMeSerializer
from .barbero import (
    BarberoPublicSerializer, BarberoDetailSerializer, BarberoMeSerializer,
    HorarioInlineSerializer, ServicioOfrecidoInlineSerializer,
)

__all__ = [
    'RegisterSerializer', 'LoginSerializer', 'UsuarioMeSerializer',
    'TurnoListSerializer', 'TurnoUpdateEstadoSerializer', 'ServicioMasSolicitadoSerializer',
    'ClienteMeSerializer',
    'BarberoPublicSerializer', 'BarberoDetailSerializer', 'BarberoMeSerializer',
    'HorarioInlineSerializer', 'ServicioOfrecidoInlineSerializer',
]
