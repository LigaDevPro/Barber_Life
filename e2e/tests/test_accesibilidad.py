"""Accesibilidad (ACC) — WCAG 2.2 nivel AA con axe-core + Playwright.

HU: "Como usuario quiero que la aplicación sea accesible para poder usarla con
teclado, lector de pantalla o zoom". Cada pantalla principal se audita en
escritorio; criterio de aceptación: 0 violaciones critical/serious.
"""
import os

import pytest

from pages.auditoria_axe import AuditoriaAxe

API_URL = os.environ.get('API_URL', 'http://localhost:8000/api').rstrip('/')
BARBERO_EMAIL = os.environ.get('BARBERO_EMAIL', 'barbero@barberlife.com')
BARBERO_PASSWORD = os.environ.get('BARBERO_PASSWORD', 'barbero1234')

# (nombre, rol, ruta, título esperado)
PANTALLAS = [
    ('login', None, '/login', 'Iniciar sesión'),
    ('registro', None, '/register', 'Crear cuenta'),
    ('inicio', 'cliente', '/inicio', 'Inicio'),
    ('solicitar-turno', 'cliente', '/solicitar-turno', 'Solicitar turno'),
    ('mis-turnos', 'cliente', '/mis-turnos', 'Mis turnos'),
    ('perfil-cliente', 'cliente', '/perfil', 'Mi perfil'),
    ('notificaciones', 'cliente', '/notificaciones', 'Notificaciones'),
    ('dashboard', 'barbero', '/dashboard', 'Dashboard'),
    ('gestion-turnos', 'barbero', '/turnos', 'Gestión de turnos'),
    ('catalogo', 'barbero', '/catalogo', 'Catálogo'),
    ('perfil-barbero', 'barbero', '/perfil', 'Mi perfil'),
]
IDS = [p[0] for p in PANTALLAS]


@pytest.fixture
def auditoria(page, base_url):
    return AuditoriaAxe(page, base_url, API_URL)


def _entrar(auditoria, rol, cliente_nuevo):
    if rol == 'cliente':
        auditoria.iniciar_sesion_por_api(cliente_nuevo['email'], cliente_nuevo['password'])
    elif rol == 'barbero':
        auditoria.iniciar_sesion_por_api(BARBERO_EMAIL, BARBERO_PASSWORD)


@pytest.mark.parametrize('nombre, rol, ruta, titulo', PANTALLAS, ids=IDS)
def test_acc_01_sin_violaciones_axe_criticas_ni_serias(auditoria, cliente_nuevo, nombre, rol, ruta, titulo):
    """ACC-01 · WCAG 2.2 AA (1.1.1, 1.3.1, 1.4.3 contraste, 2.4.x, 4.1.2 y demás reglas wcag2a/2aa/21aa/22aa de axe-core) · 0 violaciones critical/serious."""
    # Arrange
    _entrar(auditoria, rol, cliente_nuevo)

    # Act
    auditoria.abrir(ruta)
    violaciones = auditoria.violaciones_bloqueantes()

    # Assert
    detalle = [f"{v['id']} ({v['impact']}): {v['help']}" for v in violaciones]
    assert not violaciones, f'{nombre}: {detalle}'


@pytest.mark.parametrize('nombre, rol, ruta, titulo', PANTALLAS, ids=IDS)
def test_acc_02_titulo_por_ruta_e_idioma_espanol(auditoria, cliente_nuevo, nombre, rol, ruta, titulo):
    """ACC-02 · WCAG 2.4.2 y 3.1.1 · cada ruta tiene un <title> propio y la página declara lang="es"."""
    # Arrange
    _entrar(auditoria, rol, cliente_nuevo)

    # Act
    auditoria.abrir(ruta)

    # Assert
    assert auditoria.idioma() == 'es'
    assert titulo in auditoria.titulo()
    assert auditoria.titulo() != 'Barber Life'


@pytest.mark.parametrize('nombre, rol, ruta, titulo', PANTALLAS, ids=IDS)
def test_acc_03_reflow_320px_sin_scroll_horizontal(auditoria, cliente_nuevo, nombre, rol, ruta, titulo):
    """ACC-03 · WCAG 1.4.10 Reflow · a 320 px de ancho no hay scroll horizontal."""
    # Arrange
    _entrar(auditoria, rol, cliente_nuevo)
    auditoria.ajustar_ancho(320)

    # Act
    auditoria.abrir(ruta)

    # Assert
    assert not auditoria.tiene_scroll_horizontal()
