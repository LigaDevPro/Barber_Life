from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, LoginView, MeView,
    DashboardView, TurnosListView, TurnoDetailView, ServiciosMasSolicitadosView,
)

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/me/', MeView.as_view(), name='auth-me'),

    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # Turnos
    path('turnos/', TurnosListView.as_view(), name='turnos-list'),
    path('turnos/<int:pk>/', TurnoDetailView.as_view(), name='turnos-detail'),
    path('turnos/servicios-mas-solicitados/', ServiciosMasSolicitadosView.as_view(), name='servicios-mas-solicitados'),
]
