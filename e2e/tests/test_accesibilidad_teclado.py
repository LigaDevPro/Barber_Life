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


def test_a11y_12_el_foco_pasa_al_titulo_al_cambiar_de_vista(page, base_url, cliente_nuevo):
    """A11Y-12 · WCAG 2.4.3 · al navegar a otra vista el foco queda en su <h1>."""
    # Arrange
    inicio = LoginPage(page, base_url).abrir().iniciar_sesion_como_cliente(
        cliente_nuevo['email'], cliente_nuevo['password'],
    )

    # Act
    solicitud = inicio.ir_a_solicitar_turno()

    # Assert
    assert solicitud.foco_esta_en_el_titulo()


def test_a11y_13_la_opcion_elegida_se_anuncia_como_presionada(page, base_url, cliente_nuevo):
    """A11Y-13 · WCAG 4.1.2 · el servicio y la forma de pago elegidos exponen aria-pressed."""
    # Arrange
    inicio = LoginPage(page, base_url).abrir().iniciar_sesion_como_cliente(
        cliente_nuevo['email'], cliente_nuevo['password'],
    )
    solicitud = inicio.ir_a_solicitar_turno()

    # Act
    solicitud.elegir_servicio('Corte de pelo')
    solicitud.pagar_en_el_local()

    # Assert
    assert solicitud.servicios_marcados_como_elegidos() == 1
    assert solicitud.pago_en_local_esta_marcado()
