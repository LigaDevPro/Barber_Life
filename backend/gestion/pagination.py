from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PaginacionEstandar(PageNumberPagination):
    """Paginación compartida por los listados que pueden crecer mucho
    (turnos, notificaciones, reseñas). Los catálogos chicos (barberos,
    servicios, horarios, barbero-servicio) no la usan a propósito."""
    page_size = 7
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'page': self.page.number,
            'num_pages': self.page.paginator.num_pages,
            'results': data,
        })
