"""
Perfiles: Cliente (`clientes/me/`) y Barbero (`barberos/`,
`barberos/<id>/`, `barberos/me/`). Solo los casos que importan.
"""
from django.urls import reverse

from .base import BarberLifeTestCase


class PerfilClienteTests(BarberLifeTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('clientes-me')
        self.cliente = self.crear_cliente()

    def test_get_devuelve_el_perfil_propio(self):
        # Arrange
        self.crear_cliente()  # otro cliente: no tiene que filtrarse
        self.autenticar(self.cliente.usuario)

        # Act
        resp = self.client.get(self.url)

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['id'], self.cliente.id)
        self.assertEqual(resp.data['usuario']['email'], self.cliente.usuario.email)

    def test_patch_actualiza_campos_editables_e_ignora_los_protegidos(self):
        # Arrange
        self.autenticar(self.cliente.usuario)

        # Act
        resp = self.client.patch(self.url, {
            'telefono': '3511234567', 'fecha_nacimiento': '1995-04-20',
            'activo': False, 'usuario': {'rol': 'admin'},
        }, format='json')

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.cliente.refresh_from_db()
        self.cliente.usuario.refresh_from_db()
        self.assertEqual(self.cliente.usuario.telefono, '3511234567')
        self.assertEqual(str(self.cliente.fecha_nacimiento), '1995-04-20')
        self.assertTrue(self.cliente.activo)
        self.assertEqual(self.cliente.usuario.rol, 'cliente')

    def test_rol_equivocado_o_sin_token_no_accede(self):
        # Act & Assert
        self.assertEqual(self.client.get(self.url).status_code, 401)

        for usuario in (self.crear_barbero().usuario, self.crear_admin()):
            with self.subTest(rol=usuario.rol):
                self.autenticar(usuario)
                self.assertEqual(self.client.get(self.url).status_code, 404)
                self.assertEqual(
                    self.client.patch(self.url, {'telefono': '1'}, format='json').status_code, 404,
                )


class BarberosPublicosTests(BarberLifeTestCase):
    def test_listado_publico_solo_activos_y_sin_paginar(self):
        # Arrange
        activos = [self.crear_barbero() for _ in range(9)]  # más que PAGE_SIZE (7)
        self.crear_barbero(activo=False)

        # Act
        resp = self.client.get(reverse('barberos-list'))

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.data, list)
        self.assertEqual({b['id'] for b in resp.data}, {b.id for b in activos})

    def test_detalle_solo_trae_horarios_y_ofertas_activos(self):
        # Arrange
        barbero = self.crear_barbero()
        servicio = self.crear_servicio(nombre='Corte', precio='4000.00')
        horario = self.crear_horario(barbero, dia_semana=2)
        horario_off = self.crear_horario(barbero, dia_semana=3, activo=False)
        oferta = self.crear_oferta(barbero, servicio, horario, precio_personalizado='6500.00')
        self.crear_oferta(barbero, self.crear_servicio(), horario, activo=False)
        self.crear_oferta(barbero, servicio, horario_off)  # horario inactivo

        # Act
        data = self.client.get(reverse('barberos-detail', args=[barbero.id])).data

        # Assert
        self.assertEqual([h['id'] for h in data['horarios']], [horario.id])
        self.assertEqual([s['id'] for s in data['servicios_ofrecidos']], [oferta.id])
        self.assertEqual(str(data['servicios_ofrecidos'][0]['precio']), '6500.00')
        self.assertIn(data['servicios_ofrecidos'][0]['horario'], {h['id'] for h in data['horarios']})

    def test_detalle_de_barbero_inactivo_o_inexistente_da_404(self):
        # Arrange
        inactivo = self.crear_barbero(activo=False)

        # Act & Assert
        self.assertEqual(self.client.get(reverse('barberos-detail', args=[inactivo.id])).status_code, 404)
        self.assertEqual(self.client.get(reverse('barberos-detail', args=[999999])).status_code, 404)

    def test_detalle_no_tiene_n_mas_1(self):
        # Arrange
        barbero = self.crear_barbero()
        horario = self.crear_horario(barbero)
        self.crear_oferta(barbero, self.crear_servicio(), horario)
        url = reverse('barberos-detail', args=[barbero.id])

        # Act & Assert
        with self.assertNumQueries(3):  # barbero+usuario, horarios, ofertas+servicio
            self.client.get(url)

        # Arrange
        for _ in range(5):
            self.crear_oferta(barbero, self.crear_servicio(), horario)

        # Act & Assert
        with self.assertNumQueries(3):
            self.client.get(url)


class PerfilBarberoTests(BarberLifeTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('barberos-me')
        self.barbero = self.crear_barbero()

    def test_get_devuelve_el_perfil_propio_y_no_el_detalle_de_otro(self):
        # Arrange
        self.crear_barbero()
        self.autenticar(self.barbero.usuario)

        # Act
        resp = self.client.get(self.url)

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['id'], self.barbero.id)

    def test_patch_actualiza_foto_e_ignora_campos_protegidos(self):
        # Arrange
        self.autenticar(self.barbero.usuario)

        # Act
        resp = self.client.patch(
            self.url, {'foto_perfil_url': 'https://img.test/foto.jpg', 'activo': False}, format='json',
        )

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.barbero.refresh_from_db()
        self.assertEqual(self.barbero.foto_perfil_url, 'https://img.test/foto.jpg')
        self.assertTrue(self.barbero.activo)

    def test_rol_equivocado_o_sin_token_no_accede(self):
        # Act & Assert
        self.assertEqual(self.client.get(self.url).status_code, 401)

        # Arrange
        self.autenticar(self.crear_cliente().usuario)

        # Act & Assert
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(
            self.client.patch(self.url, {'foto_perfil_url': 'https://a.b/c'}, format='json').status_code, 404,
        )
