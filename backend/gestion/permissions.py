"""
Permisos DRF — implementan la Matriz de Control de Acceso de la wiki
ESTRUCTURA-Y-ARQUITECTURA (sección "Sistema de Roles y Permisos (RBAC)").

Esto es el segundo escalón de seguridad descripto en la wiki:
  JWT Middleware -> 401 si token inválido
  Role Check     -> 403 si no tiene permiso   (implementado acá, a nivel de vista,
                                                que es más preciso que un middleware
                                                genérico porque cada endpoint tiene
                                                una regla distinta)
  Vista
"""
from rest_framework.permissions import BasePermission


class EsAdministrador(BasePermission):
    """Solo Administrador. Usado en Analytics/KPIs (acceso exclusivo admin)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.rol == 'admin')


class EsBarberoOAdmin(BasePermission):
    """Barbero o Administrador. Usado en Dashboard y Gestión de Turnos."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.rol in ('barbero', 'admin')
        )


class EsClienteOAdmin(BasePermission):
    """Cliente o Administrador. Usado en reserva/cancelación de turnos propios."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.rol in ('cliente', 'admin')
        )
