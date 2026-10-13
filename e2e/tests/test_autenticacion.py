"""Flujo crítico 1 — Autenticación (AUT-E2E).

HU: "Como usuario quiero iniciar sesión para acceder a mis funciones".
"""
import pytest

from pages.login_page import LoginPage

PASSWORD_INCORRECTA = 'Password-incorrecta-1'


def test_tc_login_01_cliente_inicia_sesion_y_llega_a_inicio(page, base_url, cliente_nuevo):
    """TC-LOGIN-01 · HU Iniciar sesión · login exitoso de un cliente."""
    # Arrange
    login = LoginPage(page, base_url).abrir()

    # Act
    inicio = login.iniciar_sesion_como_cliente(cliente_nuevo['email'], cliente_nuevo['password'])

    # Assert
    assert inicio.titulo() == 'Tu turno, sin vueltas.'


@pytest.mark.parametrize(
    'caso, email, password, mensaje',
    [
        ('password_incorrecta', 'USAR_CLIENTE', PASSWORD_INCORRECTA, 'Email o contraseña incorrectos.'),
        ('email_inexistente', 'no.existe.e2e@mail.com', 'Cualquier-1234', 'Email o contraseña incorrectos.'),
        ('email_con_formato_invalido', 'esto-no-es-un-email', 'Cualquier-1234', 'Ingresá un email válido.'),
        ('password_vacia', 'USAR_CLIENTE', '', 'La contraseña es obligatoria.'),
    ],
)
def test_tc_login_02_login_invalido_muestra_error(page, base_url, cliente_nuevo, caso, email, password, mensaje):
    """TC-LOGIN-02 · HU Iniciar sesión · credenciales inválidas (4 combinaciones)."""
    # Arrange
    email = cliente_nuevo['email'] if email == 'USAR_CLIENTE' else email
    login = LoginPage(page, base_url).abrir()

    # Act
    login.intentar_login(email, password)

    # Assert
    assert login.mensaje_de_error() == mensaje
    assert '/login' in page.url
