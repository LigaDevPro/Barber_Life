from django.urls import path

from ..views import BarberoListView, BarberoDetailView, BarberoMeView

urlpatterns = [
    # 'me/' antes de '<int:pk>/': aunque el conversor int no matchearía "me"
    # igual, se deja explícito para que el orden de lectura sea obvio.
    path('barberos/me/', BarberoMeView.as_view(), name='barberos-me'),
    path('barberos/', BarberoListView.as_view(), name='barberos-list'),
    path('barberos/<int:pk>/', BarberoDetailView.as_view(), name='barberos-detail'),
]
