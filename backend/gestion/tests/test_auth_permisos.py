"""
Test de autenticación, RoleCheckMiddleware y permisos por rol.

Casos importantes: registro/login/refresh, el middleware JWT (token ausente,
inválido o expirado; rutas públicas; lectura pública de catálogos; `/me/`
siempre privado) y el 403 por rol a nivel vista.
"""
from datetime import timedelta

import jwt as pyjwt
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from gestion.models import Cliente, Usuario

from .base import BarberLifeTestCase


class RegisterTests(BarberLifeTestCase):
    def payload(self, **extra):
        data = {
            'email': 'nuevo@test.com',
            'password': 'Clave-segura-987',
            'password_confirm': 'Clave-segura-987',
        }
        data.update(extra)
        return data

    def test_registro_ok_crea_cliente_y_fuerza_rol_cliente(self):
        # Act
        # Aunque el body mande rol=admin, la cuenta nace como cliente.
        resp = self.client.post(
            reverse('auth-register'), self.payload(rol='admin'), format='json',
        )

        # Assert
        self.assertEqual(resp.status_code, 201)
        usuario = Usuario.objects.get(email='nuevo@test.com')
        self.assertEqual(usuario.rol, Usuario.Rol.CLIENTE)
        self.assertTrue(Cliente.objects.filter(usuario=usuario).exists())
        self.assertEqual(len(self.notificaciones_de(usuario, 'bienvenida')), 1)

    def test_registro_rechaza_email_duplicado_y_passwords_distintas(self):
        # Arrange
        self.crear_usuario(email='nuevo@test.com')

        # Act & Assert
        with self.subTest('email duplicado (sin distinguir mayúsculas)'):
            resp = self.client.post(
                reverse('auth-register'), self.payload(email='NUEVO@test.com'), format='json',
            )
            self.assertEqual(resp.status_code, 400)
            self.assertIn('email', resp.data)

        with self.subTest('passwords distintas'):
            resp = self.client.post(
                reverse('auth-register'),
                self.payload(email='otro@test.com', password_confirm='Otra-clave-123'),
                format='json',
            )
            self.assertEqual(resp.status_code, 400)
            self.assertIn('password_confirm', resp.data)
            self.assertFalse(Usuario.objects.filter(email='otro@test.com').exists())


class LoginRefreshTests(BarberLifeTestCase):
    def login(self, email, password=None):
        return self.client.post(
            reverse('auth-login'),
            {'email': email, 'password': password or self.PASSWORD},
            format='json',
        )

    def test_login_ok_devuelve_tokens_y_rol_y_el_access_sirve(self):
        # Arrange
        barbero = self.crear_barbero()

        # Act
        resp = self.login(barbero.usuario.email)

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['access'])
        self.assertTrue(resp.data['refresh'])
        self.assertEqual(resp.data['usuario']['rol'], 'barbero')

        # Arrange
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")

        # Act & Assert
        self.assertEqual(self.client.get(reverse('auth-me')).status_code, 200)

    def test_login_con_credenciales_malas_da_mensaje_generico(self):
        # Arrange
        cliente = self.crear_cliente()
        inactivo = self.crear_cliente(estado=Usuario.Estado.INACTIVO)

        # Act
        casos = {
            'password incorrecta': self.login(cliente.usuario.email, 'otra-clave'),
            'email inexistente': self.login('no-existe@test.com'),
            # Sin la contraseña correcta, un inactivo es indistinguible de
            # cualquier otro: no se filtra que la cuenta existe.
            'inactivo con password incorrecta': self.login(inactivo.usuario.email, 'otra-clave'),
        }

        # Assert
        for nombre, resp in casos.items():
            with self.subTest(nombre):
                self.assertEqual(resp.status_code, 400)
                self.assertNotIn('access', resp.data)
                self.assertEqual(resp.data['non_field_errors'], ['Email o contraseña incorrectos.'])

    def test_login_de_usuario_inactivo_con_password_correcta_dice_cuenta_inactiva(self):
        # Arrange
        inactivo = self.crear_cliente(estado=Usuario.Estado.INACTIVO)

        # Act
        resp = self.login(inactivo.usuario.email)

        # Assert
        self.assertEqual(resp.status_code, 400)
        self.assertNotIn('access', resp.data)
        self.assertEqual(resp.data['non_field_errors'], ['La cuenta está inactiva.'])

    def test_login_acepta_email_con_tilde(self):
        """TA-BE-104 | HU US05 / RF21 | TEST-L-001 | Regresión del bug #47."""
        # Arrange
        usuario = self.crear_usuario(email='usuario.maría@barberlife.com')

        # Act
        resp = self.login('usuario.maría@barberlife.com')

        # Assert
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertIn('access', resp.data)
        self.assertEqual(resp.data['usuario']['email'], usuario.email)

    def test_usuario_inactivo_no_puede_usar_un_token_ya_emitido(self):
        # Arrange
        # El backend ahora deja autenticar a inactivos; esto asegura que la
        # API siga cerrada para ellos (JWTAuthentication revisa is_active).
        cliente = self.crear_cliente()
        self.autenticar(cliente.usuario)

        # Act & Assert
        self.assertEqual(self.client.get(reverse('auth-me')).status_code, 200)

        # Arrange
        cliente.usuario.estado = Usuario.Estado.INACTIVO
        cliente.usuario.save()

        # Act & Assert
        self.assertEqual(self.client.get(reverse('auth-me')).status_code, 401)

    def test_refresh_devuelve_nuevo_access(self):
        # Arrange
        cliente = self.crear_cliente()

        # Act
        refresh = self.login(cliente.usuario.email).data['refresh']

        resp = self.client.post(reverse('auth-refresh'), {'refresh': refresh}, format='json')

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['access'])


class RoleCheckMiddlewareTests(BarberLifeTestCase):
    def test_ruta_protegida_sin_token_es_401(self):
        # Act & Assert
        for nombre in ('auth-me', 'turnos-list', 'dashboard', 'pagos-list', 'notificaciones-list'):
            with self.subTest(ruta=nombre):
                self.assertEqual(self.client.get(reverse(nombre)).status_code, 401)

    def test_token_invalido_firma_ajena_o_expirado_es_401(self):
        # Arrange
        usuario = self.crear_usuario()
        casos = {
            'basura': 'esto.no.es.un.jwt',
            'firma ajena': pyjwt.encode(
                {'user_id': usuario.id, 'exp': timezone.now() + timedelta(hours=1)},
                'otra-secret-key', algorithm='HS256',
            ),
            'expirado': pyjwt.encode(
                {'user_id': usuario.id, 'token_type': 'access',
                 'exp': timezone.now() - timedelta(minutes=1)},
                settings.SECRET_KEY, algorithm='HS256',
            ),
        }

        # Act & Assert
        for nombre, token in casos.items():
            with self.subTest(nombre):
                self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
                self.assertEqual(self.client.get(reverse('auth-me')).status_code, 401)

    def test_rutas_publicas_no_exigen_token(self):
        # Act & Assert
        # Alcanza con que el middleware no corte con su 401: el resto lo
        # resuelve cada vista (el webhook responde 200 aunque venga vacío).
        for nombre in ('auth-register', 'auth-login', 'auth-refresh', 'pagos-webhook'):
            with self.subTest(ruta=nombre):
                resp = self.client.post(reverse(nombre), {}, format='json')
                self.assertNotEqual(resp.status_code, 401)

    def test_catalogos_lectura_publica_pero_escritura_exige_token(self):
        # Arrange
        urls = tuple(reverse(n) for n in ('barberos-list', 'servicios-list', 'barbero-servicio-list', 'resenas-list'))

        # Act & Assert
        for url in urls:
            with self.subTest(url=url, metodo='get'):
                self.assertEqual(self.client.get(url).status_code, 200)
            for metodo in ('post', 'patch', 'delete'):
                with self.subTest(url=url, metodo=metodo):
                    resp = getattr(self.client, metodo)(url, {}, format='json')
                    self.assertEqual(resp.status_code, 401)

    def test_me_es_privado_aunque_comparta_prefijo_publico(self):
        # Act & Assert
        with self.subTest('sin token'):
            self.assertEqual(self.client.get(reverse('barberos-me')).status_code, 401)

        with self.subTest('con token de barbero'):
            self.autenticar(self.crear_barbero().usuario)
            self.assertEqual(self.client.get(reverse('barberos-me')).status_code, 200)


class PermisosPorRolTests(BarberLifeTestCase):
    def test_cliente_recibe_403_en_endpoints_de_barbero_y_admin(self):
        # Arrange
        self.autenticar(self.crear_cliente().usuario)

        casos = (
            ('get', reverse('dashboard')),
            ('get', reverse('turnos-list')),
            ('post', reverse('servicios-list')),
        )

        # Act & Assert
        for metodo, url in casos:
            with self.subTest(metodo=metodo, url=url):
                resp = getattr(self.client, metodo)(url, {}, format='json')
                self.assertEqual(resp.status_code, 403)

    def test_barbero_no_crea_servicios_ni_reserva_como_cliente(self):
        # Arrange
        self.autenticar(self.crear_barbero().usuario)

        casos = (
            ('post', reverse('servicios-list')),
            ('post', reverse('turnos-list')),
            ('get', reverse('pagos-list')),
        )

        # Act & Assert
        for metodo, url in casos:
            with self.subTest(metodo=metodo, url=url):
                resp = getattr(self.client, metodo)(url, {}, format='json')
                self.assertEqual(resp.status_code, 403)
