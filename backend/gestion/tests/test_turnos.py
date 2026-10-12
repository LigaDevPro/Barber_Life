"""
Turnos: reserva, agenda, cambio de estado, cancelación y ranking.

Cubre views/turno.py + serializers/turno.py + las reglas de negocio de
`Turno` (ventana de cancelación, solapamiento, sincronización del pago).
Enfocado en los casos críticos, no en cada variante.
"""
from datetime import date, datetime, time, timedelta
from unittest import mock

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from gestion.models import Barbero, Pago, Turno

from .base import BarberLifeTestCase


class TurnosBase(BarberLifeTestCase):
    def congelar_ahora(self, fecha, hora):
        """Fija `timezone.now()` en fecha+hora (hora local, tz-aware)."""
        ahora = timezone.make_aware(datetime.combine(fecha, hora))
        patcher = mock.patch('django.utils.timezone.now', return_value=ahora)
        patcher.start()
        self.addCleanup(patcher.stop)
        return ahora

    def reservar(self, esc, **extra):
        payload = {
            'barbero': esc['barbero'].id,
            'servicio': esc['servicio'].id,
            'fecha_turno': esc['fecha'].isoformat(),
            'hora_inicio': '10:00',
        }
        payload.update(extra)
        return self.client.post(reverse('turnos-list'), payload, format='json')


# ---------------------------------------------------------------------------
# POST /api/turnos/ — reserva
# ---------------------------------------------------------------------------

class ReservaTurnoTests(TurnosBase):
    def test_reserva_ok_calcula_hora_fin_y_notifica_al_barbero(self):
        esc = self.escenario_reservable()
        esc['servicio'].duracion_minutos = 45
        esc['servicio'].save()
        self.autenticar(esc['cliente'].usuario)

        resp = self.reservar(esc)

        self.assertEqual(resp.status_code, 201, resp.data)
        turno = Turno.objects.get(pk=resp.data['id'])
        self.assertEqual(turno.hora_fin, time(10, 45))
        self.assertEqual(turno.estado, Turno.Estado.PENDIENTE)
        self.assertEqual(turno.cliente, esc['cliente'])
        self.assertEqual(len(self.notificaciones_de(esc['barbero'].usuario, 'nuevo_turno')), 1)

    def test_admin_sin_perfil_cliente_recibe_400_no_500(self):
        esc = self.escenario_reservable()
        self.autenticar(self.crear_admin())

        resp = self.reservar(esc)

        self.assertEqual(resp.status_code, 400)
        self.assertIn('detail', resp.data)

    def test_barbero_o_servicio_inactivo(self):
        esc = self.escenario_reservable()
        self.autenticar(esc['cliente'].usuario)

        esc['barbero'].activo = False
        esc['barbero'].save()
        resp = self.reservar(esc)
        self.assertEqual(resp.status_code, 400)
        self.assertIn('barbero', resp.data)

        esc['barbero'].activo = True
        esc['barbero'].save()
        esc['servicio'].activo = False
        esc['servicio'].save()
        resp = self.reservar(esc)
        self.assertEqual(resp.status_code, 400)
        self.assertIn('servicio', resp.data)

    def test_fecha_en_el_pasado(self):
        esc = self.escenario_reservable()
        pasada = date.today() - timedelta(days=6)
        horario = self.crear_horario(esc['barbero'], dia_semana=pasada.isoweekday())
        self.crear_oferta(esc['barbero'], esc['servicio'], horario)
        self.autenticar(esc['cliente'].usuario)

        resp = self.reservar(esc, fecha_turno=pasada.isoformat())

        self.assertEqual(resp.status_code, 400)
        self.assertIn('fecha_turno', resp.data)

    def test_turno_que_cruza_medianoche(self):
        esc = self.escenario_reservable()
        esc['servicio'].duracion_minutos = 60
        esc['servicio'].save()
        self.autenticar(esc['cliente'].usuario)

        resp = self.reservar(esc, hora_inicio='23:30')

        self.assertEqual(resp.status_code, 400)
        self.assertIn('hora_inicio', resp.data)

    def test_barbero_no_ofrece_el_servicio(self):
        esc = self.escenario_reservable()
        otro_servicio = self.crear_servicio()
        self.autenticar(esc['cliente'].usuario)

        resp = self.reservar(esc, servicio=otro_servicio.id)

        self.assertEqual(resp.status_code, 400)
        self.assertIn('servicio', resp.data)

    def test_solapamiento_con_turno_existente(self):
        esc = self.escenario_reservable()
        otro = self.crear_cliente()
        self.crear_turno(otro, esc['barbero'], esc['servicio'], esc['fecha'], hora_inicio=time(10, 0))
        self.autenticar(esc['cliente'].usuario)

        resp = self.reservar(esc, hora_inicio='10:15')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Turno.objects.count(), 1)

    def test_create_bloquea_la_fila_del_barbero(self):
        """Protección contra la race condition (TOCTOU): la creación tiene
        que hacer SELECT ... FOR UPDATE sobre Barbero, no sobre Turno."""
        esc = self.escenario_reservable()
        self.autenticar(esc['cliente'].usuario)

        with CaptureQueriesContext(connection) as ctx:
            resp = self.reservar(esc)

        self.assertEqual(resp.status_code, 201, resp.data)
        locks = [q['sql'] for q in ctx.captured_queries if 'FOR UPDATE' in q['sql']]
        self.assertEqual(len(locks), 1, locks)
        self.assertIn(Barbero._meta.db_table, locks[0])


# ---------------------------------------------------------------------------
# Listados: agenda del barbero y "mis turnos" del cliente
# ---------------------------------------------------------------------------

class ListadosTurnosTests(TurnosBase):
    def setUp(self):
        super().setUp()
        self.servicio = self.crear_servicio()
        self.barbero_a = self.crear_barbero()
        self.barbero_b = self.crear_barbero()
        self.cliente_a = self.crear_cliente()
        self.cliente_b = self.crear_cliente()
        self.turno_a = self.crear_turno(self.cliente_a, self.barbero_a, self.servicio)
        self.turno_b = self.crear_turno(self.cliente_b, self.barbero_b, self.servicio)

    def test_barbero_ve_solo_su_agenda_aunque_pase_otro_id(self):
        self.autenticar(self.barbero_a.usuario)

        resp = self.client.get(reverse('turnos-list'), {'barbero': self.barbero_b.id})

        self.assertEqual(resp.status_code, 200)
        self.assertEqual({t['id'] for t in resp.data['results']}, {self.turno_a.id})

    def test_mis_turnos_aisla_por_cliente(self):
        self.autenticar(self.cliente_a.usuario)

        resp = self.client.get(reverse('turnos-mis-turnos'))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual({t['id'] for t in resp.data['results']}, {self.turno_a.id})


# ---------------------------------------------------------------------------
# PATCH /api/turnos/<id>/ — cambio de estado (barbero/admin)
# ---------------------------------------------------------------------------

class CambioEstadoTurnoTests(TurnosBase):
    def setUp(self):
        super().setUp()
        self.barbero = self.crear_barbero()
        self.cliente = self.crear_cliente()
        self.turno = self.crear_turno(self.cliente, self.barbero, self.crear_servicio())

    def patch(self, estado):
        return self.client.patch(reverse('turnos-detail', args=[self.turno.id]), {'estado': estado}, format='json')

    def test_barbero_ajeno_recibe_403(self):
        self.autenticar(self.crear_barbero().usuario)

        resp = self.patch('confirmado')

        self.assertEqual(resp.status_code, 403)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, Turno.Estado.PENDIENTE)

    def test_cancelar_por_patch_sincroniza_el_pago_a_reembolsado(self):
        pago = self.crear_pago(self.turno, estado=Pago.Estado.APROBADO)
        self.autenticar(self.barbero.usuario)

        resp = self.patch('cancelado')

        self.assertEqual(resp.status_code, 200, resp.data)
        pago.refresh_from_db()
        self.assertEqual(pago.estado, Pago.Estado.REEMBOLSADO)

    def test_estado_invalido_devuelve_400_con_mensaje_propio(self):
        """TA-BE-105 | HU US09 / RF11 | TEST-T-006 | Regresión del bug #49."""
        # Arrange
        self.autenticar(self.barbero.usuario)

        # Act
        resp = self.patch('INVALID_STATUS')

        # Assert
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Estado inválido', str(resp.data['estado'][0]))
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, Turno.Estado.PENDIENTE)


# ---------------------------------------------------------------------------
# PATCH /api/turnos/<id>/cancelar/
# ---------------------------------------------------------------------------

class CancelarTurnoTests(TurnosBase):
    def setUp(self):
        super().setUp()
        self.barbero = self.crear_barbero()
        self.cliente = self.crear_cliente()
        self.fecha = self.fecha_futura()
        self.turno = self.crear_turno(
            self.cliente, self.barbero, self.crear_servicio(), self.fecha, hora_inicio=time(12, 0))

    def cancelar(self):
        return self.client.patch(reverse('turnos-cancelar', args=[self.turno.id]))

    def test_cliente_duenio_dentro_de_la_ventana(self):
        self.congelar_ahora(self.fecha, time(9, 0))  # faltan 3hs > 2hs
        self.autenticar(self.cliente.usuario)

        resp = self.cancelar()

        self.assertEqual(resp.status_code, 200, resp.data)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, Turno.Estado.CANCELADO)
        self.assertEqual(len(self.notificaciones_de(self.barbero.usuario, 'turno_cancelado')), 1)

    def test_fuera_de_la_ventana_devuelve_403(self):
        self.congelar_ahora(self.fecha, time(11, 0))  # falta 1h < 2hs
        self.autenticar(self.cliente.usuario)

        resp = self.cancelar()

        self.assertEqual(resp.status_code, 403)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, Turno.Estado.PENDIENTE)

    def test_turno_ya_pagado_devuelve_403_para_el_cliente(self):
        self.crear_pago(self.turno, estado=Pago.Estado.APROBADO)
        self.congelar_ahora(self.fecha, time(9, 0))
        self.autenticar(self.cliente.usuario)

        self.assertEqual(self.cancelar().status_code, 403)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, Turno.Estado.PENDIENTE)

    def test_cliente_ajeno_recibe_403(self):
        self.congelar_ahora(self.fecha, time(9, 0))
        self.autenticar(self.crear_cliente().usuario)

        self.assertEqual(self.cancelar().status_code, 403)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, Turno.Estado.PENDIENTE)

    def test_turno_completado_o_cancelado_devuelve_400_incluso_al_admin(self):
        admin = self.crear_admin()
        for estado in (Turno.Estado.COMPLETADO, Turno.Estado.CANCELADO):
            self.turno.estado = estado
            self.turno.save()

            self.autenticar(self.cliente.usuario)
            self.assertEqual(self.cancelar().status_code, 400, estado)
            self.autenticar(admin)
            self.assertEqual(self.cancelar().status_code, 400, estado)

    def test_admin_cancela_fuera_de_ventana_y_sincroniza_el_pago(self):
        pago = self.crear_pago(self.turno, estado=Pago.Estado.APROBADO)
        self.congelar_ahora(self.fecha, time(11, 30))  # falta 30', ya pagado
        self.autenticar(self.crear_admin())

        resp = self.cancelar()

        self.assertEqual(resp.status_code, 200, resp.data)
        self.turno.refresh_from_db()
        pago.refresh_from_db()
        self.assertEqual(self.turno.estado, Turno.Estado.CANCELADO)
        self.assertEqual(pago.estado, Pago.Estado.REEMBOLSADO)


# ---------------------------------------------------------------------------
# GET /api/turnos/servicios-mas-solicitados/
# ---------------------------------------------------------------------------

class ServiciosMasSolicitadosTests(TurnosBase):
    def test_ranking_ordenado_sin_cancelados_y_acotado_al_barbero(self):
        barbero_a = self.crear_barbero()
        barbero_b = self.crear_barbero()
        cliente = self.crear_cliente()
        corte = self.crear_servicio(nombre='Corte')
        barba = self.crear_servicio(nombre='Barba')
        tinte = self.crear_servicio(nombre='Tinte')
        for h in (9, 10, 11):
            self.crear_turno(cliente, barbero_a, corte, hora_inicio=time(h, 0))
        self.crear_turno(cliente, barbero_a, barba, hora_inicio=time(12, 0))
        self.crear_turno(cliente, barbero_a, tinte, hora_inicio=time(13, 0), estado=Turno.Estado.CANCELADO)
        self.crear_turno(cliente, barbero_b, barba, hora_inicio=time(9, 0))
        self.autenticar(barbero_a.usuario)

        resp = self.client.get(reverse('servicios-mas-solicitados'))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual([(r['nombre'], r['cantidad']) for r in resp.data], [('Corte', 3), ('Barba', 1)])
