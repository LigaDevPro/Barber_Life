"""
Re-exporta todas las views para que `gestion/urls.py` (y cualquier otro
código) pueda seguir haciendo `from gestion.views import X` sin saber en qué
submódulo vive cada clase. Cada dominio vive en su propio archivo para que
distintas personas puedan trabajar en paralelo sin pisarse en el mismo
archivo.
"""
from .auth import RegisterView, LoginView, MeView
from .dashboard import DashboardView
from .turno import (
    TurnosListView, TurnoDetailView, TurnoCancelarView, ServiciosMasSolicitadosView, TurnosPagination,
)
from .cliente import ClienteMeView
from .barbero import BarberoListView, BarberoDetailView, BarberoMeView
from .catalogo import (
    ServicioListCreateView, ServicioDetailView,
    HorarioListCreateView, HorarioDetailView,
    BarberoServicioListCreateView, BarberoServicioDetailView,
)
from .pago import PagoListCreateView, PagoWebhookView
from .notificacion import NotificacionListView, NotificacionLeidaView

__all__ = [
    'RegisterView', 'LoginView', 'MeView',
    'DashboardView',
    'TurnosListView', 'TurnoDetailView', 'TurnoCancelarView', 'ServiciosMasSolicitadosView', 'TurnosPagination',
    'ClienteMeView',
    'BarberoListView', 'BarberoDetailView', 'BarberoMeView',
    'ServicioListCreateView', 'ServicioDetailView',
    'HorarioListCreateView', 'HorarioDetailView',
    'BarberoServicioListCreateView', 'BarberoServicioDetailView',
    'PagoListCreateView', 'PagoWebhookView',
    'NotificacionListView', 'NotificacionLeidaView',
]
