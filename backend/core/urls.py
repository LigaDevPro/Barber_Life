from django.contrib import admin
from django.conf import settings
from django.http import HttpResponse
from django.urls import path, include, re_path
from django.views.static import serve

def servir_media(request, path):
    # document_root se lee en cada request (y no al importar) para poder
    # cambiar MEDIA_ROOT en los tests.
    return serve(request, path, document_root=settings.MEDIA_ROOT)


def health(request):
    # Endpoint liviano para que un cron externo mantenga despierto el servicio
    # en Render (plan gratis). No toca la base de datos.
    return HttpResponse('ok')


urlpatterns = [
    path('health/', health),
    path('admin/', admin.site.urls),
    path('api/', include('gestion.urls')),
    # Fotos subidas. Se sirven desde Django (alcanza para la entrega; en una
    # instalación grande iría detrás de nginx / un bucket).
    re_path(r'^media/(?P<path>.*)$', servir_media),
]