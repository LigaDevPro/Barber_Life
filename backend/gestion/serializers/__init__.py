"""
Re-exporta todos los serializers para que el resto del código (views, etc.)
pueda seguir haciendo `from gestion.serializers import X` sin saber en qué
submódulo vive cada clase. Cada dominio (auth, turno, cliente, barbero, ...)
vive en su propio archivo para que distintas personas puedan trabajar en
paralelo sin pisarse en el mismo archivo.
"""
from .auth import RegisterSerializer, LoginSerializer, UsuarioMeSerializer
from .turno import (
    TurnoListSerializer, TurnoCreateSerializer, TurnoUpdateEstadoSerializer,
    ServicioMasSolicitadoSerializer,
)
from .cliente import ClienteMeSerializer
from .barbero import (
    BarberoPublicSerializer, BarberoDetailSerializer, BarberoMeSerializer,
    HorarioInlineSerializer, ServicioOfrecidoInlineSerializer,
)
from .catalogo import ServicioSerializer, HorarioSerializer, BarberoServicioSerializer

__all__ = [
    'RegisterSerializer', 'LoginSerializer', 'UsuarioMeSerializer',
    'TurnoListSerializer', 'TurnoCreateSerializer', 'TurnoUpdateEstadoSerializer',
    'ServicioMasSolicitadoSerializer',
    'ClienteMeSerializer',
    'BarberoPublicSerializer', 'BarberoDetailSerializer', 'BarberoMeSerializer',
    'HorarioInlineSerializer', 'ServicioOfrecidoInlineSerializer',
    'ServicioSerializer', 'HorarioSerializer', 'BarberoServicioSerializer',
]
