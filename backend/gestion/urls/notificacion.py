from django.urls import path

from ..views import NotificacionListView, NotificacionLeidaView

urlpatterns = [
    path('notificaciones/', NotificacionListView.as_view(), name='notificaciones-list'),
    path('notificaciones/<str:id>/leida/', NotificacionLeidaView.as_view(), name='notificaciones-leida'),
]
