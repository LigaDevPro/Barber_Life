from django.urls import path

from ..views import PagoListCreateView, PagoWebhookView

urlpatterns = [
    path('pagos/', PagoListCreateView.as_view(), name='pagos-list'),
    path('pagos/webhook/', PagoWebhookView.as_view(), name='pagos-webhook'),
]
