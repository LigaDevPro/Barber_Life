from django.urls import path

from ..views import ClienteMeView

urlpatterns = [
    path('clientes/me/', ClienteMeView.as_view(), name='clientes-me'),
]
