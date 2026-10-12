"""
Smoke test de la infraestructura de tests: si esto pasa, los helpers de
`base.py` funcionan y los demás paquetes pueden apoyarse en ellos.
"""
from django.urls import reverse

from .base import BarberLifeTestCase


class InfraTests(BarberLifeTestCase):
    def test_login_con_jwt_real_y_mongo_falso(self):
        # Arrange
        cliente = self.crear_cliente()
        self.autenticar(cliente.usuario)

        # Act
        resp = self.client.get(reverse('auth-me'))

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['id'], cliente.usuario.id)

    def test_mongo_en_memoria_registra_notificaciones(self):
        # Arrange
        from gestion.mongo import registrar_notificacion

        usuario = self.crear_usuario()

        # Act
        registrar_notificacion(usuario.id, 'prueba', 'hola')

        # Assert
        self.assertEqual(len(self.notificaciones_de(usuario, 'prueba')), 1)

    def test_escenario_reservable_arma_oferta_valida(self):
        # Act
        esc = self.escenario_reservable()

        # Assert
        self.assertEqual(esc['horario'].dia_semana, esc['fecha'].isoweekday())
        self.assertTrue(esc['oferta'].activo)
