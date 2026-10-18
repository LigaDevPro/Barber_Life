"""
Emails transaccionales (gestion/emails.py).

El runner de Django reemplaza el backend de correo por uno en memoria
(`mail.outbox`), así que no se manda nada a ningún SMTP real.
Escenarios: bienvenida, reserva, cambio de estado y cancelación del cliente.
"""
from datetime import time
from unittest import mock

from django.core import mail
from django.test import override_settings
from django.urls import reverse

from gestion.models import Turno, Usuario

from .test_turnos import TurnosBase


class EmailBienvenidaTests(TurnosBase):
    def registrar(self, email='nuevo@test.com'):
        return self.client.post(reverse('auth-register'), {
            'email': email, 'password': 'Clave-segura-987', 'password_confirm': 'Clave-segura-987',
        }, format='json')

    def test_registro_envia_mail_de_bienvenida(self):
        resp = self.registrar()

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        mensaje = mail.outbox[0]
        self.assertEqual(mensaje.to, ['nuevo@test.com'])
        self.assertIn('Bienvenido', mensaje.subject)

    def test_el_mail_es_multipart_con_version_html(self):
        self.registrar()

        mensaje = mail.outbox[0]
        self.assertEqual(mensaje.alternatives[0][1], 'text/html')
        self.assertIn('Ir a Barber Life', mensaje.body)

    def test_registro_invalido_no_envia_mail(self):
        resp = self.client.post(reverse('auth-register'), {
            'email': 'x@test.com', 'password': 'Clave-segura-987', 'password_confirm': 'otra',
        }, format='json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_si_el_smtp_falla_el_registro_igual_funciona(self):
        with mock.patch('gestion.emails.EmailMultiAlternatives.send', side_effect=OSError('smtp caído')), \
                self.assertLogs('gestion.emails', level='ERROR'):
            resp = self.registrar('sinmail@test.com')

        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Usuario.objects.filter(email='sinmail@test.com').exists())


class EmailTurnosTests(TurnosBase):
    def test_reservar_turno_avisa_al_cliente(self):
        esc = self.escenario_reservable()
        self.autenticar(esc['cliente'].usuario)

        resp = self.reservar(esc)

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(len(mail.outbox), 1)
        mensaje = mail.outbox[0]
        self.assertEqual(mensaje.to, [esc['cliente'].usuario.email])
        self.assertIn('reservaste', mensaje.subject.lower())
        self.assertIn(esc['servicio'].nombre, mensaje.body)
        self.assertIn('10:00', mensaje.body)

    def test_reserva_rechazada_no_envia_mail(self):
        esc = self.escenario_reservable()
        self.autenticar(esc['cliente'].usuario)

        resp = self.reservar(esc, hora_inicio='03:00')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_cambio_de_estado_avisa_al_cliente(self):
        barbero = self.crear_barbero()
        cliente = self.crear_cliente()
        turno = self.crear_turno(cliente, barbero, self.crear_servicio(), hora_inicio=time(12, 0))
        self.autenticar(barbero.usuario)

        resp = self.client.patch(
            reverse('turnos-detail', args=[turno.id]), {'estado': Turno.Estado.CONFIRMADO}, format='json')

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [cliente.usuario.email])
        self.assertIn('Confirmado', mail.outbox[0].subject)

    def test_cancelacion_del_cliente_avisa_al_barbero(self):
        barbero = self.crear_barbero()
        cliente = self.crear_cliente()
        fecha = self.fecha_futura()
        turno = self.crear_turno(cliente, barbero, self.crear_servicio(), fecha, hora_inicio=time(12, 0))
        self.congelar_ahora(fecha, time(9, 0))
        self.autenticar(cliente.usuario)

        resp = self.client.patch(reverse('turnos-cancelar', args=[turno.id]))

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [barbero.usuario.email])
        self.assertIn('canceló', mail.outbox[0].subject)

    def test_cancelacion_denegada_no_envia_mail(self):
        barbero = self.crear_barbero()
        cliente = self.crear_cliente()
        fecha = self.fecha_futura()
        turno = self.crear_turno(cliente, barbero, self.crear_servicio(), fecha, hora_inicio=time(12, 0))
        self.congelar_ahora(fecha, time(11, 0))  # falta 1h < 2h
        self.autenticar(cliente.usuario)

        resp = self.client.patch(reverse('turnos-cancelar', args=[turno.id]))

        self.assertEqual(resp.status_code, 403)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(DEFAULT_FROM_EMAIL='Barber Life <no-reply@test.com>')
    def test_usa_el_remitente_configurado(self):
        self.client.post(reverse('auth-register'), {
            'email': 'r@test.com', 'password': 'Clave-segura-987', 'password_confirm': 'Clave-segura-987',
        }, format='json')

        self.assertEqual(mail.outbox[0].from_email, 'Barber Life <no-reply@test.com>')
