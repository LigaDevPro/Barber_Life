"""
AUT-BE: verbos HTTP no permitidos (405) y acceso anónimo (401) por recurso.

Las URLs se obtienen con reverse(). Para el 405 se autentica un admin, porque
DRF resuelve primero autenticación y permisos y recién después el verbo.
"""
from django.urls import reverse

from .base import BarberLifeTestCase


class MetodosNoPermitidosTests(BarberLifeTestCase):
    # (nombre de la URL, args, verbos que el recurso NO admite)
    CASOS = [
        ('auth-login', [], ('get', 'put', 'delete')),
        ('auth-me', [], ('post', 'delete')),
        ('barberos-list', [], ('post', 'put', 'delete')),
        ('servicios-list', [], ('put', 'patch', 'delete')),
        ('servicios-detail', [1], ('post',)),
        ('horarios-list', [], ('put', 'patch', 'delete')),
        ('horarios-detail', [1], ('post',)),
        ('barbero-servicio-list', [], ('put', 'patch', 'delete')),
        ('barbero-servicio-detail', [1], ('post',)),
        ('turnos-list', [], ('put', 'patch', 'delete')),
        ('turnos-mis-turnos', [], ('post', 'put', 'delete')),
        ('turnos-detail', [1], ('post',)),
        ('notificaciones-list', [], ('post', 'put', 'delete')),
        ('resenas-list', [], ('put', 'patch', 'delete')),
        ('pagos-list', [], ('put', 'patch', 'delete')),
        ('dashboard', [], ('post', 'put', 'delete')),
    ]

    def test_verbos_no_permitidos_devuelven_405(self):
        # Arrange
        self.autenticar(self.crear_admin())

        for nombre, args, verbos in self.CASOS:
            for verbo in verbos:
                with self.subTest(url=nombre, verbo=verbo):
                    url = reverse(nombre, args=args)

                    # Act
                    resp = getattr(self.client, verbo)(url, {}, format='json')

                    # Assert
                    self.assertEqual(resp.status_code, 405)

    def test_anonimo_devuelve_401_en_recursos_protegidos(self):
        # Arrange
        self.desautenticar()

        for nombre in ('auth-me', 'turnos-list', 'turnos-mis-turnos',
                       'pagos-list', 'notificaciones-list', 'dashboard'):
            with self.subTest(url=nombre):
                # Act
                resp = self.client.get(reverse(nombre))

                # Assert
                self.assertEqual(resp.status_code, 401)
