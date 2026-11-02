from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from ..views import (
    RegisterView, LoginView, GoogleLoginView, MeView, RecuperarContrasenaView, RestablecerContrasenaView,
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/google/', GoogleLoginView.as_view(), name='auth-google'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('auth/password-reset/', RecuperarContrasenaView.as_view(), name='auth-password-reset'),
    path('auth/password-reset/confirm/', RestablecerContrasenaView.as_view(), name='auth-password-reset-confirm'),
]
