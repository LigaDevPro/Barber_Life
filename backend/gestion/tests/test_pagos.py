"""
Pagos: creación de preferencia, listado, webhook de Mercado Pago y
cliente `mercadopago_client`. Enfocado en los casos que importan: dinero,
ownership, idempotencia del webhook y manejo de errores de MP.
"""
from unittest import mock

from django.test import override_settings
from django.urls import reverse

from gestion.mercadopago_client import MercadoPagoError, crear_preferencia, obtener_pago
from gestion.models import Pago, Turno

from .base import BarberLifeTestCase


class PagoBaseCase(BarberLifeTestCase):
    def setUp(self):
        super().setUp()
        self.esc = self.escenario_reservable()
        self.cliente = self.esc['cliente']
        self.turno = self.crear_turno(
            self.cliente, self.esc['barbero'], self.esc['servicio'], fecha_turno=self.esc['fecha'],
        )


class CrearPagoTests(PagoBaseCase):
    url = reverse('pagos-list')

    def test_cliente_crea_pago_y_recibe_init_point(self):
        self.autenticar(self.cliente.usuario)

        resp = self.client.post(self.url, {'turno': self.turno.id}, format='json')

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['init_point'], 'https://mp.test/checkout/pref-test-123')
        pago = Pago.objects.get(turno=self.turno)
        self.assertEqual(pago.transaccion_id, 'pref-test-123')
        self.assertEqual(pago.estado, Pago.Estado.PENDIENTE)
        self.assertEqual(str(pago.monto_total), '5000.00')

    def test_monto_usa_precio_personalizado_de_la_oferta(self):
        oferta = self.esc['oferta']
        oferta.precio_personalizado = '7777.00'
        oferta.save()
        self.autenticar(self.cliente.usuario)

        self.client.post(self.url, {'turno': self.turno.id}, format='json')

        self.assertEqual(str(Pago.objects.get(turno=self.turno).monto_total), '7777.00')

    def test_turno_de_otro_cliente_es_403(self):
        self.autenticar(self.crear_cliente().usuario)

        resp = self.client.post(self.url, {'turno': self.turno.id}, format='json')

        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Pago.objects.filter(turno=self.turno).exists())
        self.mp_crear_preferencia.assert_not_called()

    def test_turno_que_ya_tiene_pago_es_400(self):
        self.crear_pago(self.turno)
        self.autenticar(self.cliente.usuario)

        resp = self.client.post(self.url, {'turno': self.turno.id}, format='json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Pago.objects.filter(turno=self.turno).count(), 1)

    def test_error_de_mercado_pago_es_502_y_no_deja_el_pago(self):
        self.mp_crear_preferencia.side_effect = MercadoPagoError('boom')
        self.autenticar(self.cliente.usuario)

        resp = self.client.post(self.url, {'turno': self.turno.id}, format='json')

        self.assertEqual(resp.status_code, 502)
        self.assertFalse(Pago.objects.filter(turno=self.turno).exists())


class ListarPagosTests(PagoBaseCase):
    def test_cliente_ve_solo_sus_pagos(self):
        propio = self.crear_pago(self.turno)
        otro = self.crear_cliente()
        turno_ajeno = self.crear_turno(
            otro, self.esc['barbero'], self.esc['servicio'], fecha_turno=self.esc['fecha'],
            hora_inicio=self.turno.hora_fin,
        )
        self.crear_pago(turno_ajeno)
        self.autenticar(self.cliente.usuario)

        resp = self.client.get(reverse('pagos-list'))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual([p['id'] for p in resp.data], [propio.id])


class WebhookTests(PagoBaseCase):
    url = reverse('pagos-webhook')

    def setUp(self):
        super().setUp()
        self.pago = self.crear_pago(self.turno, transaccion_id='pref-test-123')
        self.mp_obtener_pago.return_value = {
            'id': 987654, 'status': 'approved', 'external_reference': str(self.turno.id),
        }

    def _notificar(self):
        return self.client.post(self.url, {'type': 'payment', 'data': {'id': '987654'}}, format='json')

    def _recargar(self):
        self.turno.refresh_from_db()
        self.pago.refresh_from_db()

    def test_aprobado_confirma_turno_notifica_y_guarda_id_real(self):
        # Sin token: el webhook es público (lo llama Mercado Pago).
        resp = self._notificar()

        self.assertEqual(resp.status_code, 200)
        self._recargar()
        self.assertEqual(self.pago.estado, Pago.Estado.APROBADO)
        self.assertIsNotNone(self.pago.fecha_pago)
        self.assertEqual(self.pago.transaccion_id, '987654')
        self.assertEqual(self.turno.estado, Turno.Estado.CONFIRMADO)
        self.assertEqual(len(self.notificaciones_de(self.cliente.usuario, 'pago_aprobado')), 1)

    def test_rechazado_cancela_el_turno(self):
        self.mp_obtener_pago.return_value['status'] = 'rejected'

        self._notificar()

        self._recargar()
        self.assertEqual(self.pago.estado, Pago.Estado.RECHAZADO)
        self.assertEqual(self.turno.estado, Turno.Estado.CANCELADO)
        self.assertEqual(len(self.notificaciones_de(self.cliente.usuario, 'pago_rechazado')), 1)

    def test_reintento_de_mp_no_duplica_la_notificacion(self):
        self._notificar()
        self._notificar()

        self._recargar()
        self.assertEqual(self.pago.estado, Pago.Estado.APROBADO)
        self.assertEqual(len(self.notificaciones_de(self.cliente.usuario, 'pago_aprobado')), 1)

    def test_notificacion_que_no_es_de_pago_se_ignora(self):
        resp = self.client.post(self.url, {'type': 'merchant_order', 'data': {'id': '1'}}, format='json')

        self.assertEqual(resp.status_code, 200)
        self.mp_obtener_pago.assert_not_called()
        self._recargar()
        self.assertEqual(self.pago.estado, Pago.Estado.PENDIENTE)

    def test_turno_inexistente_responde_200_sin_tocar_nada(self):
        self.mp_obtener_pago.return_value['external_reference'] = '999999'

        resp = self._notificar()

        self.assertEqual(resp.status_code, 200)
        self._recargar()
        self.assertEqual(self.pago.estado, Pago.Estado.PENDIENTE)

    def test_turno_cancelado_no_se_reabre_al_aprobarse_el_pago(self):
        self.turno.estado = Turno.Estado.CANCELADO
        self.turno.save()

        self._notificar()

        self._recargar()
        self.assertEqual(self.turno.estado, Turno.Estado.CANCELADO)
        self.assertEqual(self.notificaciones_de(self.cliente.usuario, 'pago_aprobado'), [])


class MercadoPagoClientTests(PagoBaseCase):
    """`gestion/mercadopago_client.py` con el SDK mockeado."""

    def _sdk(self):
        patcher = mock.patch('gestion.mercadopago_client.mercadopago.SDK')
        sdk_cls = patcher.start()
        self.addCleanup(patcher.stop)
        return sdk_cls, sdk_cls.return_value

    @override_settings(MERCADOPAGO_ACCESS_TOKEN='')
    def test_sin_token_levanta_error_sin_llamar_al_sdk(self):
        sdk_cls, _ = self._sdk()

        with self.assertRaises(MercadoPagoError):
            crear_preferencia(self.turno)
        sdk_cls.assert_not_called()

    @override_settings(MERCADOPAGO_ACCESS_TOKEN='TEST-token')
    def test_status_inesperado_de_mp_levanta_error(self):
        _, sdk = self._sdk()
        sdk.payment.return_value.get.return_value = {'status': 404, 'response': {}}

        with self.assertRaises(MercadoPagoError):
            obtener_pago('5')

    @override_settings(MERCADOPAGO_ACCESS_TOKEN='TEST-token')
    def test_preferencia_lleva_external_reference_y_precio(self):
        _, sdk = self._sdk()
        sdk.preference.return_value.create.return_value = {'status': 201, 'response': {'id': 'pref-1'}}

        crear_preferencia(self.turno)

        datos = sdk.preference.return_value.create.call_args.args[0]
        self.assertEqual(datos['external_reference'], str(self.turno.id))
        self.assertEqual(datos['items'][0]['unit_price'], 5000.0)

    def _datos_preferencia(self):
        _, sdk = self._sdk()
        sdk.preference.return_value.create.return_value = {'status': 201, 'response': {'id': 'p'}}
        crear_preferencia(self.turno)
        return sdk.preference.return_value.create.call_args.args[0]

    @override_settings(
        MERCADOPAGO_ACCESS_TOKEN='TEST-token',
        FRONTEND_URL='https://app.test/', BACKEND_PUBLIC_URL='https://api.test/',
    )
    def test_preferencia_envia_back_urls_auto_return_y_notification_url(self):
        datos = self._datos_preferencia()

        self.assertEqual(datos['back_urls'], {
            'success': 'https://app.test/pago/resultado?estado=exito',
            'failure': 'https://app.test/pago/resultado?estado=fallo',
            'pending': 'https://app.test/pago/resultado?estado=pendiente',
        })
        self.assertEqual(datos['auto_return'], 'approved')
        self.assertEqual(datos['notification_url'], 'https://api.test/api/pagos/webhook/')

    @override_settings(
        MERCADOPAGO_ACCESS_TOKEN='TEST-token',
        FRONTEND_URL='http://localhost:4200', BACKEND_PUBLIC_URL='',
    )
    def test_en_local_no_manda_auto_return_ni_notification_url(self):
        # MP rechaza auto_return con back_urls locales y no puede llamar a
        # localhost: sin URLs públicas la preferencia igual tiene que crearse.
        datos = self._datos_preferencia()

        self.assertIn('back_urls', datos)
        self.assertNotIn('auto_return', datos)
        self.assertNotIn('notification_url', datos)
