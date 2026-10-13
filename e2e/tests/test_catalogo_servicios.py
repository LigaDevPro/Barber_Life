"""Flujo crítico 2 — CRUD del módulo principal: catálogo de servicios (AUT-E2E).

HU: "Como administrador quiero gestionar los servicios que ofrece la barbería".
"""
import uuid

from pages.login_page import LoginPage


def test_tc_catalogo_01_admin_crea_edita_y_desactiva_un_servicio(page, base_url, credenciales_admin):
    """TC-CATALOGO-01 · HU Gestionar servicios · alta, edición y baja lógica."""
    # Arrange
    nombre = f'E2E Servicio {uuid.uuid4().hex[:6]}'
    dashboard = LoginPage(page, base_url).abrir().iniciar_sesion_como_staff(
        credenciales_admin['email'], credenciales_admin['password'],
    )
    catalogo = dashboard.ir_a_catalogo()

    # Act + Assert · alta
    catalogo.crear_servicio(nombre, duracion=25, precio='12.50')
    detalle = catalogo.detalle_de(nombre)
    assert '25 min' in detalle and '$12.50' in detalle

    # Act + Assert · edición
    catalogo.editar_precio(nombre, '18.00')
    assert '$18.00' in catalogo.detalle_de(nombre)

    # Act + Assert · baja lógica (el servicio queda en la lista como inactivo)
    catalogo.desactivar_servicio(nombre)
    assert 'inactivo' in catalogo.detalle_de(nombre)
    assert catalogo.cantidad_de(nombre) == 1
