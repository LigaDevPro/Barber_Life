from django.urls import path

from ..views import (
    ServicioListCreateView, ServicioDetailView,
    HorarioListCreateView, HorarioDetailView,
    BarberoServicioListCreateView, BarberoServicioDetailView,
)

urlpatterns = [
    path('servicios/', ServicioListCreateView.as_view(), name='servicios-list'),
    path('servicios/<int:pk>/', ServicioDetailView.as_view(), name='servicios-detail'),

    path('horarios/', HorarioListCreateView.as_view(), name='horarios-list'),
    path('horarios/<int:pk>/', HorarioDetailView.as_view(), name='horarios-detail'),

    path('barbero-servicio/', BarberoServicioListCreateView.as_view(), name='barbero-servicio-list'),
    path('barbero-servicio/<int:pk>/', BarberoServicioDetailView.as_view(), name='barbero-servicio-detail'),
]
