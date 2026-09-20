from django.urls import path

from ..views import TurnosListView, TurnoDetailView, ServiciosMasSolicitadosView

urlpatterns = [
    path('turnos/', TurnosListView.as_view(), name='turnos-list'),
    path('turnos/<int:pk>/', TurnoDetailView.as_view(), name='turnos-detail'),
    path('turnos/servicios-mas-solicitados/', ServiciosMasSolicitadosView.as_view(), name='servicios-mas-solicitados'),
]
