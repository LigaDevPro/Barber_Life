"""
Login / registro con Google (POST /api/auth/google/).

La verificación del ID token contra los servidores de Google se reemplaza por
un mock (`id_token.verify_oauth2_token`): los tests no salen a internet. Se
comprueba que la vista le pase NUESTRO client id como audience y se cubren los
errores que levanta la librería (firma, vencimiento, audience).
"""
from unittest import mock

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from google.auth import exceptions as google_exceptions

from gestion.models import Cliente, Usuario

from .base import BarberLifeTestCase

CLIENT_ID = 'cliente-de-prueba.apps.googleusercontent.com'


def datos_google(**extra):
    datos = {
        'iss': 'https://accounts.google.com', 'aud': CLIENT_ID, 'sub': '1234567890',
        'email': 'nuevo@gmail.com', 'email_verified': True,
        'given_name': 'Nico', 'family_name': 'Pérez',
    }
    datos.update(extra)
    return datos


@override_settings(GOOGLE_CLIENT_ID=CLIENT_ID)
class LoginGoogleTests(BarberLifeTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('auth-google')

    def entrar(self, datos=None, error=None, credencial='token-de-google'):
        efecto = {'side_effect': error} if error else {'return_value': datos or datos_google()}
        with mock.patch('gestion.google_auth.id_token.verify_oauth2_token', **efecto) as verificar:
            self.verificar = verificar
            return self.client.post(self.url, {'credential': credencial}, format='json')

    def test_primer_ingreso_crea_un_cliente(self):
        resp = self.entrar()

        self.assertEqual(resp.status_code, 200, resp.data)
        usuario = Usuario.objects.get(email='nuevo@gmail.com')
        self.assertEqual(usuario.rol, Usuario.Rol.CLIENTE)
        self.assertEqual((usuario.first_name, usuario.last_name), ('Nico', 'Pérez'))
        self.assertTrue(Cliente.objects.filter(usuario=usuario).exists())
        self.assertFalse(usuario.has_usable_password())
        self.assertEqual(resp.data['usuario']['email'], 'nuevo@gmail.com')
        self.assertEqual(resp.data['usuario']['rol'], 'cliente')
        self.assertTrue(resp.data['access'] and resp.data['refresh'])

    def test_verifica_contra_nuestro_client_id(self):
        self.entrar()

        _, args, _ = self.verificar.mock_calls[0]
        self.assertEqual(args[0], 'token-de-google')
        self.assertEqual(args[2], CLIENT_ID)

    def test_el_token_emitido_sirve_para_la_api(self):
        resp = self.entrar()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')
        me = self.client.get(reverse('auth-me'))

        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data['email'], 'nuevo@gmail.com')

    def test_el_alta_manda_bienvenida_y_deja_registro(self):
        resp = self.entrar()

        usuario = Usuario.objects.get(pk=resp.data['usuario']['id'])
        self.assertEqual(len(self.notificaciones_de(usuario, 'bienvenida')), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['nuevo@gmail.com'])
        self.assertEqual(len(self.eventos_log('registro_google')), 1)

    def test_segundo_ingreso_reutiliza_la_cuenta(self):
        self.entrar()
        mail.outbox.clear()

        resp = self.entrar()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Usuario.objects.filter(email='nuevo@gmail.com').count(), 1)
        self.assertEqual(len(mail.outbox), 0)  # sin segundo mail de bienvenida
        self.assertEqual(len(self.eventos_log('login_google')), 1)

    def test_entra_a_la_cuenta_existente_con_ese_correo_sin_importar_mayusculas(self):
        cliente = self.crear_cliente(email='Ana@Gmail.com')

        resp = self.entrar(datos_google(email='ana@gmail.com'))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['usuario']['id'], cliente.usuario_id)
        self.assertEqual(Usuario.objects.filter(email__iexact='ana@gmail.com').count(), 1)

    def test_conserva_el_rol_de_una_cuenta_existente(self):
        barbero = self.crear_barbero(email='barbero@gmail.com')

        resp = self.entrar(datos_google(email='barbero@gmail.com'))

        self.assertEqual(resp.data['usuario']['rol'], 'barbero')
        self.assertEqual(resp.data['usuario']['id'], barbero.usuario_id)

    def test_el_rol_no_se_puede_pedir_desde_el_request(self):
        with mock.patch('gestion.google_auth.id_token.verify_oauth2_token', return_value=datos_google()):
            self.client.post(self.url, {'credential': 'x', 'rol': 'admin'}, format='json')

        self.assertEqual(Usuario.objects.get(email='nuevo@gmail.com').rol, Usuario.Rol.CLIENTE)

    def test_cuenta_inactiva_no_entra(self):
        self.crear_cliente(email='baja@gmail.com', estado='inactivo')

        resp = self.entrar(datos_google(email='baja@gmail.com'))

        self.assertEqual(resp.status_code, 400)
        self.assertIn('inactiva', str(resp.data))

    def test_credencial_invalida_o_vencida(self):
        resp = self.entrar(error=ValueError('Token expired'))

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_token_emitido_para_otra_app(self):
        resp = self.entrar(error=ValueError('Token has wrong audience otra-app, expected one of [...]'))

        self.assertEqual(resp.status_code, 400)

    def test_token_mal_formado_con_la_libreria_real(self):
        # Sin mock: la librería real rechaza estos tokens antes de salir a internet.
        for basura in ('basura', 'a.b.c'):
            resp = self.client.post(self.url, {'credential': basura}, format='json')

            self.assertEqual(resp.status_code, 400, basura)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_error_de_google_auth_no_termina_en_500(self):
        resp = self.entrar(error=google_exceptions.MalformedError('Could not verify token signature.'))

        self.assertEqual(resp.status_code, 400)

    def test_si_google_no_responde_devuelve_503(self):
        resp = self.entrar(error=google_exceptions.TransportError('sin conexión'))

        self.assertEqual(resp.status_code, 503)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_correo_no_verificado_se_rechaza(self):
        resp = self.entrar(datos_google(email_verified=False))

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_falta_la_credencial(self):
        resp = self.client.post(self.url, {}, format='json')

        self.assertEqual(resp.status_code, 400)
        self.assertIn('credential', resp.data)

    def test_la_cuenta_creada_con_google_no_entra_con_contrasena(self):
        self.entrar()

        resp = self.client.post(reverse('auth-login'), {'email': 'nuevo@gmail.com', 'password': 'cualquiera123'}, format='json')

        self.assertEqual(resp.status_code, 400)

    def test_es_publico_no_pide_token(self):
        self.client.credentials()  # sin Authorization

        resp = self.entrar()

        self.assertEqual(resp.status_code, 200)

    def test_get_no_permitido(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)


class GoogleSinConfigurarTests(BarberLifeTestCase):
    @override_settings(GOOGLE_CLIENT_ID='')
    def test_sin_client_id_responde_503(self):
        resp = self.client.post(reverse('auth-google'), {'credential': 'x'}, format='json')

        self.assertEqual(resp.status_code, 503)
        self.assertEqual(Usuario.objects.count(), 0)
