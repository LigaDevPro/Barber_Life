from django.urls import path

from ..views import ResenaListCreateView

urlpatterns = [
    path('resenas/', ResenaListCreateView.as_view(), name='resenas-list'),
]
