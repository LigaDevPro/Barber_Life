"""Accesibilidad con teclado (ACC) — flujo del diálogo de perfil de barbero.

HU: "Como cliente quiero ver el perfil de un barbero y cerrarlo sin mouse".
Criterios WCAG 2.1.2 (sin trampa de teclado) y 2.4.3 (orden del foco).
"""
from pages.login_page import LoginPage


def _abrir_perfil_de_barbero(page, base_url, cliente_nuevo):
    login = LoginPage(page, base_url).abrir()
    inicio = login.iniciar_sesion_como_cliente(cliente_nuevo['email'], cliente_nuevo['password'])
    inicio.abrir_perfil_del_primer_barbero()
    return inicio


def test_acc_04_el_foco_entra_al_dialogo_y_tab_no_escapa(page, base_url, cliente_nuevo):
    """ACC-04 · WCAG 2.4.3 · al abrir el perfil del barbero el foco queda dentro y Tab no sale."""
    # Arrange
    inicio = _abrir_perfil_de_barbero(page, base_url, cliente_nuevo)

    # Act
    inicio.recorrer_con_tab(6)

    # Assert
    assert inicio.foco_esta_dentro_del_dialogo()


def test_acc_05_escape_cierra_el_dialogo(page, base_url, cliente_nuevo):
    """ACC-05 · WCAG 2.1.2 · la tecla Esc cierra el perfil del barbero."""
    # Arrange
    inicio = _abrir_perfil_de_barbero(page, base_url, cliente_nuevo)

    # Act
    inicio.cerrar_con_escape()

    # Assert
    assert not inicio.dialogo_esta_abierto()
