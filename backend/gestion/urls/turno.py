from django.urls import path

from ..views import TurnosListView, TurnoDetailView, TurnoCancelarView, ServiciosMasSolicitadosView, MisTurnosView

urlpatterns = [
    path('turnos/', TurnosListView.as_view(), name='turnos-list'),
    path('turnos/servicios-mas-solicitados/', ServiciosMasSolicitadosView.as_view(), name='servicios-mas-solicitados'),
    path('turnos/mis-turnos/', MisTurnosView.as_view(), name='turnos-mis-turnos'),
    path('turnos/<int:pk>/', TurnoDetailView.as_view(), name='turnos-detail'),
    path('turnos/<int:pk>/cancelar/', TurnoCancelarView.as_view(), name='turnos-cancelar'),
]
