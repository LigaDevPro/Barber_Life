"""Flujo crítico 3 — Reserva de un turno por un cliente (AUT-E2E).

HU: "Como cliente quiero solicitar un turno eligiendo servicio, barbero y horario".
Requiere datos de `manage.py seed_demo` (barbero con horarios y servicios).
"""
from datetime import datetime

import pytest

from pages.login_page import LoginPage


def test_tc_turno_01_cliente_solicita_un_turno_pagando_en_el_local(page, base_url, cliente_nuevo):
    """TC-TURNO-01 · HU Solicitar turno · reserva completa con pago en el local."""
    # Arrange
    inicio = LoginPage(page, base_url).abrir().iniciar_sesion_como_cliente(
        cliente_nuevo['email'], cliente_nuevo['password'],
    )
    solicitud = inicio.ir_a_solicitar_turno()

    # Act
    solicitud.elegir_servicio('Corte de pelo')
    solicitud.elegir_primer_barbero()
    solicitud.elegir_ultimo_dia_y_primer_horario()
    solicitud.pagar_en_el_local()
    solicitud.confirmar()

    # Assert
    assert solicitud.titulo_de_confirmacion() == 'Solicitaste tu turno'


@pytest.mark.xfail(reason='BUG: la pantalla ofrece horarios de hoy que ya pasaron y el backend responde 400', strict=True)
def test_tc_turno_02_no_ofrece_horarios_que_ya_pasaron(page, base_url, cliente_nuevo):
    """TC-TURNO-02 · HU Solicitar turno · no se pueden elegir horarios en el pasado."""
    # Arrange
    ahora = datetime.now()
    solicitud = LoginPage(page, base_url).abrir().iniciar_sesion_como_cliente(
        cliente_nuevo['email'], cliente_nuevo['password'],
    ).ir_a_solicitar_turno()
    solicitud.elegir_servicio('Corte de pelo')
    solicitud.elegir_primer_barbero()

    # Act
    horarios = solicitud.horarios_ofrecidos_hoy(ahora.day)

    # Assert
    if not horarios:
        pytest.skip('Hoy no es un día con horarios cargados')
    ya_pasados = [h for h in horarios if h < ahora.strftime('%H:%M')]
    assert ya_pasados == [], f'Se ofrecen horarios pasados: {ya_pasados}'
