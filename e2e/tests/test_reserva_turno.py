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
    solicitud.pagar_en_el_local()
    solicitud.reservar_primer_horario_disponible()

    # Assert
    assert solicitud.titulo_de_confirmacion() == 'Solicitaste tu turno'


def test_tc_turno_02_no_ofrece_horarios_que_ya_pasaron(page, base_url, cliente_nuevo):
    """TC-TURNO-02 · HU Solicitar turno · para hoy solo se ofrecen horarios futuros."""
    # Arrange: el reloj del navegador queda fijo hoy a las 14:00, así el test
    # no depende de la hora real en la que se ejecuta.
    ahora = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
    page.clock.set_fixed_time(ahora)
    solicitud = LoginPage(page, base_url).abrir().iniciar_sesion_como_cliente(
        cliente_nuevo['email'], cliente_nuevo['password'],
    ).ir_a_solicitar_turno()
    solicitud.elegir_servicio('Corte de pelo')
    solicitud.elegir_primer_barbero()

    # Act
    horarios = solicitud.horarios_ofrecidos_hoy(ahora.day)

    # Assert
    if horarios is None:
        pytest.skip('Hoy no es un día con horarios cargados')
    assert horarios, 'Hoy deberían quedar horarios después de las 14:00'
    ya_pasados = [h for h in horarios if h <= ahora.strftime('%H:%M')]
    assert ya_pasados == [], f'Se ofrecen horarios pasados: {ya_pasados}'
