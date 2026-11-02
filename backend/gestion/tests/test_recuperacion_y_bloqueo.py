"""
US05 — Recuperación de contraseña y bloqueo tras intentos fallidos.

Escenarios del Product Backlog (US05):
  * tras 3 intentos fallidos el login queda bloqueado 15 minutos;
  * el usuario puede pedir un enlace por email y elegir una contraseña nueva.

El correo va a `mail.outbox` (backend en memoria del runner de Django).
"""
import re
import time
from unittest import mock

from django.core import mail
from django.test import override_settings
from django.urls import reverse

from gestion.models import Usuario

from .base import BarberLifeTestCase

GENERICO = 'Email o contraseña incorrectos.'


class BloqueoPorIntentosTests(BarberLifeTestCase):
    def login(self, email, password='Clave-incorrecta-1'):
        return self.client.post(reverse('auth-login'), {'email': email, 'password': password}, format='json')

    def test_dos_intentos_fallidos_dan_el_mensaje_generico(self):
        # Arrange
        cliente = self.crear_cliente()

        # Act
        respuestas = [self.login(cliente.usuario.email) for _ in range(2)]

        # Assert
        for resp in respuestas:
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.data['non_field_errors'], [GENERICO])

    def test_al_tercer_intento_fallido_la_cuenta_queda_bloqueada(self):
        # Arrange
        cliente = self.crear_cliente()
        for _ in range(2):
            self.login(cliente.usuario.email)

        # Act
        tercero = self.login(cliente.usuario.email)
        con_clave_correcta = self.login(cliente.usuario.email, self.PASSWORD)

        # Assert
        self.assertEqual(tercero.status_code, 400)
        self.assertIn('Demasiados intentos fallidos', tercero.data['non_field_errors'][0])
        self.assertEqual(con_clave_correcta.status_code, 400)
        self.assertNotIn('access', con_clave_correcta.data)
        self.assertIn('Demasiados intentos fallidos', con_clave_correcta.data['non_field_errors'][0])

    def test_un_login_correcto_reinicia_el_contador(self):
        # Arrange
        cliente = self.crear_cliente()
        email = cliente.usuario.email
        self.login(email)
        self.login(email)

        # Act
        ok = self.login(email, self.PASSWORD)
        despues = [self.login(email) for _ in range(2)]

        # Assert
        self.assertEqual(ok.status_code, 200)
        for resp in despues:
            self.assertEqual(resp.data['non_field_errors'], [GENERICO])

    def test_el_bloqueo_vence_a_los_15_minutos(self):
        # Arrange
        cliente = self.crear_cliente()
        for _ in range(3):
            self.login(cliente.usuario.email)
        dentro_de_16_minutos = time.time() + 16 * 60

        # Act
        with mock.patch('time.time', return_value=dentro_de_16_minutos):
            resp = self.login(cliente.usuario.email, self.PASSWORD)

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.data)

    def test_el_bloqueo_no_revela_si_el_email_existe(self):
        # Arrange
        cliente = self.crear_cliente()

        # Act
        existente = [self.login(cliente.usuario.email) for _ in range(3)][-1]
        inexistente = [self.login('nadie@barberlife.com') for _ in range(3)][-1]

        # Assert
        self.assertEqual(existente.data, inexistente.data)

    def test_el_bloqueo_es_por_email_y_no_afecta_a_otras_cuentas(self):
        # Arrange
        bloqueado = self.crear_cliente()
        otro = self.crear_cliente()
        for _ in range(3):
            self.login(bloqueado.usuario.email)

        # Act
        resp = self.login(otro.usuario.email, self.PASSWORD)

        # Assert
        self.assertEqual(resp.status_code, 200)

    @override_settings(LOGIN_MAX_INTENTOS=5)
    def test_la_cantidad_de_intentos_se_configura_por_settings(self):
        # Arrange
        cliente = self.crear_cliente()

        # Act
        respuestas = [self.login(cliente.usuario.email) for _ in range(4)]

        # Assert
        self.assertEqual(respuestas[-1].data['non_field_errors'], [GENERICO])


class RecuperarContrasenaTests(BarberLifeTestCase):
    NUEVA = 'Nueva-clave-segura-456'

    def pedir_enlace(self, email):
        return self.client.post(reverse('auth-password-reset'), {'email': email}, format='json')

    def enlace_del_mail(self):
        return re.search(r'uid=([^&\s]+)&token=([^\s"]+)', mail.outbox[-1].body).groups()

    def confirmar(self, uid, token, password=None, password_confirm=None):
        password = password or self.NUEVA
        return self.client.post(reverse('auth-password-reset-confirm'), {
            'uid': uid, 'token': token, 'password': password, 'password_confirm': password_confirm or password,
        }, format='json')

    def test_pedir_enlace_manda_un_mail_con_el_link(self):
        # Arrange
        cliente = self.crear_cliente()

        # Act
        resp = self.pedir_enlace(cliente.usuario.email)

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [cliente.usuario.email])
        self.assertIn('/restablecer-contrasena?uid=', mail.outbox[0].body)

    def test_la_respuesta_es_igual_si_el_email_no_existe_y_no_manda_mail(self):
        # Arrange
        cliente = self.crear_cliente()

        # Act
        existente = self.pedir_enlace(cliente.usuario.email)
        inexistente = self.pedir_enlace('nadie@barberlife.com')

        # Assert
        self.assertEqual(inexistente.status_code, 200)
        self.assertEqual(existente.data, inexistente.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_una_cuenta_inactiva_no_recibe_enlace(self):
        # Arrange
        inactivo = self.crear_cliente(estado=Usuario.Estado.INACTIVO)

        # Act
        resp = self.pedir_enlace(inactivo.usuario.email)

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_con_el_enlace_se_cambia_la_contrasena_y_se_puede_entrar(self):
        # Arrange
        cliente = self.crear_cliente()
        self.pedir_enlace(cliente.usuario.email)
        uid, token = self.enlace_del_mail()

        # Act
        resp = self.confirmar(uid, token)
        login_nuevo = self.client.post(reverse('auth-login'), {
            'email': cliente.usuario.email, 'password': self.NUEVA}, format='json')
        login_viejo = self.client.post(reverse('auth-login'), {
            'email': cliente.usuario.email, 'password': self.PASSWORD}, format='json')

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(login_nuevo.status_code, 200)
        self.assertEqual(login_viejo.status_code, 400)

    def test_el_enlace_sirve_una_sola_vez(self):
        # Arrange
        cliente = self.crear_cliente()
        self.pedir_enlace(cliente.usuario.email)
        uid, token = self.enlace_del_mail()
        self.confirmar(uid, token)

        # Act
        resp = self.confirmar(uid, token, 'Otra-clave-segura-789')

        # Assert
        self.assertEqual(resp.status_code, 400)
        self.assertIn('no es válido', resp.data['non_field_errors'][0])

    def test_token_o_uid_invalidos_dan_400(self):
        # Arrange
        cliente = self.crear_cliente()
        self.pedir_enlace(cliente.usuario.email)
        uid, token = self.enlace_del_mail()

        # Act
        casos = {
            'token alterado': self.confirmar(uid, token + 'x'),
            'uid inexistente': self.confirmar('OTk5OTk5', token),
            'uid mal formado': self.confirmar('%%%', token),
        }

        # Assert
        for nombre, resp in casos.items():
            with self.subTest(nombre):
                self.assertEqual(resp.status_code, 400)

    def test_rechaza_contrasena_debil_o_que_no_coincide(self):
        # Arrange
        cliente = self.crear_cliente()
        self.pedir_enlace(cliente.usuario.email)
        uid, token = self.enlace_del_mail()

        # Act
        debil = self.confirmar(uid, token, '1234')
        distinta = self.confirmar(uid, token, self.NUEVA, 'Otra-cosa-999')

        # Assert
        self.assertEqual(debil.status_code, 400)
        self.assertIn('password', debil.data)
        self.assertEqual(distinta.status_code, 400)
        self.assertIn('password_confirm', distinta.data)

    def test_restablecer_la_contrasena_desbloquea_el_login(self):
        # Arrange
        cliente = self.crear_cliente()
        email = cliente.usuario.email
        for _ in range(3):
            self.client.post(reverse('auth-login'), {'email': email, 'password': 'mal'}, format='json')
        self.pedir_enlace(email)
        uid, token = self.enlace_del_mail()

        # Act
        self.confirmar(uid, token)
        resp = self.client.post(reverse('auth-login'), {'email': email, 'password': self.NUEVA}, format='json')

        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_los_endpoints_son_publicos(self):
        # Act
        pedido = self.pedir_enlace('alguien@barberlife.com')
        confirmacion = self.confirmar('x', 'y')

        # Assert: el middleware no exige JWT (no es 401)
        self.assertEqual(pedido.status_code, 200)
        self.assertEqual(confirmacion.status_code, 400)
