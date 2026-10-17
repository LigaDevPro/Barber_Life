"""
WebSockets: notificaciones en tiempo real (gestion/consumers.py + realtime.py).

Se usa WebsocketCommunicator de Channels contra el router real, con la capa
de canales en memoria y Mongo en memoria: no hace falta ningún servicio externo.
"""
from datetime import time
from functools import wraps
from inspect import iscoroutinefunction
from unittest import mock

from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from gestion.consumers import NotificacionesConsumer
from gestion.mongo import registrar_notificacion
from gestion.routing import websocket_urlpatterns

from .test_turnos import TurnosBase

RUTA = '/ws/notificaciones/'


def token_de(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


def _cerrando_sockets(funcion):
    @wraps(funcion)
    async def envoltura(self):
        self._abiertos = []
        try:
            await funcion(self)
        finally:
            for comunicador in self._abiertos:
                if not comunicador.future.done():
                    await comunicador.disconnect()

    return envoltura


class WebSocketBase(TurnosBase):
    def __init_subclass__(cls, **kwargs):
        """Cada test async corre en un event loop propio: se lo envuelve para
        cerrar al final los sockets que quedaron abiertos (sin tareas colgadas)."""
        super().__init_subclass__(**kwargs)
        for nombre, funcion in list(vars(cls).items()):
            if nombre.startswith('test') and iscoroutinefunction(funcion):
                setattr(cls, nombre, _cerrando_sockets(funcion))

    def setUp(self):
        super().setUp()
        # Channels cierra las conexiones "viejas" a la base después de cada
        # llamada; dentro de la transacción del test eso mataría la conexión
        # de prueba. En producción es el comportamiento correcto, acá se anula.
        parche = mock.patch('channels.db.close_old_connections')
        parche.start()
        self.addCleanup(parche.stop)

    async def conectar(self, headers=None):
        comunicador = WebsocketCommunicator(URLRouter(websocket_urlpatterns), RUTA, headers=headers)
        conectado, _ = await comunicador.connect()
        self.assertTrue(conectado)
        self._abiertos.append(comunicador)
        return comunicador

    async def conectar_autenticado(self, usuario):
        comunicador = await self.conectar()
        await comunicador.send_json_to({'type': 'auth', 'token': token_de(usuario)})
        self.assertEqual(await comunicador.receive_json_from(), {'type': 'auth_ok'})
        return comunicador

    async def assert_cierra_por_no_autorizado(self, comunicador):
        mensaje = await comunicador.receive_output()
        while mensaje['type'] == 'websocket.send':  # puede venir antes un auth_error
            mensaje = await comunicador.receive_output()
        self.assertEqual(mensaje['type'], 'websocket.close')
        self.assertEqual(mensaje['code'], 4401)


class AutenticacionSocketTests(WebSocketBase):
    async def test_token_valido_se_autentica(self):
        usuario = await sync_to_async(self.crear_cliente)()

        comunicador = await self.conectar_autenticado(usuario.usuario)


    async def test_token_invalido_cierra_con_4401(self):
        comunicador = await self.conectar()

        await comunicador.send_json_to({'type': 'auth', 'token': 'no-es-un-jwt'})

        self.assertEqual(await comunicador.receive_json_from(), {'type': 'auth_error'})
        await self.assert_cierra_por_no_autorizado(comunicador)

    async def test_un_refresh_token_no_sirve(self):
        cliente = await sync_to_async(self.crear_cliente)()
        refresh = str(RefreshToken.for_user(cliente.usuario))
        comunicador = await self.conectar()

        await comunicador.send_json_to({'type': 'auth', 'token': refresh})

        self.assertEqual(await comunicador.receive_json_from(), {'type': 'auth_error'})
        await self.assert_cierra_por_no_autorizado(comunicador)

    async def test_usuario_inactivo_se_rechaza(self):
        cliente = await sync_to_async(self.crear_cliente)()
        token = token_de(cliente.usuario)
        cliente.usuario.estado = 'inactivo'  # Usuario.save() sincroniza is_active con estado
        await sync_to_async(cliente.usuario.save)()
        comunicador = await self.conectar()

        await comunicador.send_json_to({'type': 'auth', 'token': token})

        self.assertEqual(await comunicador.receive_json_from(), {'type': 'auth_error'})
        await self.assert_cierra_por_no_autorizado(comunicador)

    async def test_otro_mensaje_antes_de_autenticar_cierra(self):
        comunicador = await self.conectar()

        await comunicador.send_json_to({'type': 'ping'})

        self.assertEqual(await comunicador.receive_json_from(), {'type': 'auth_error'})
        await self.assert_cierra_por_no_autorizado(comunicador)

    async def test_sin_autenticar_se_cierra_por_timeout(self):
        with mock.patch.object(NotificacionesConsumer, 'AUTH_TIMEOUT', 0.05):
            comunicador = await self.conectar()

            await self.assert_cierra_por_no_autorizado(comunicador)

    async def test_ping_responde_pong(self):
        cliente = await sync_to_async(self.crear_cliente)()
        comunicador = await self.conectar_autenticado(cliente.usuario)

        await comunicador.send_json_to({'type': 'ping'})

        self.assertEqual(await comunicador.receive_json_from(), {'type': 'pong'})

    async def test_rechaza_origenes_que_no_estan_en_allowed_hosts(self):
        from core.asgi import application

        comunicador = WebsocketCommunicator(application, RUTA, headers=[(b'origin', b'http://sitio-malicioso.test')])

        conectado, _ = await comunicador.connect()

        self.assertFalse(conectado)

    async def test_acepta_el_origen_del_frontend(self):
        from core.asgi import application

        comunicador = WebsocketCommunicator(application, RUTA, headers=[(b'origin', b'http://localhost:4200')])

        conectado, _ = await comunicador.connect()

        self.assertTrue(conectado)
        self._abiertos.append(comunicador)


class EmpujeEnTiempoRealTests(WebSocketBase):
    async def test_la_notificacion_llega_al_usuario_conectado(self):
        cliente = await sync_to_async(self.crear_cliente)()
        comunicador = await self.conectar_autenticado(cliente.usuario)

        await sync_to_async(registrar_notificacion)(cliente.usuario_id, 'estado_turno', 'Tu turno fue confirmado.')

        mensaje = await comunicador.receive_json_from()
        self.assertEqual(mensaje['type'], 'notificacion')
        datos = mensaje['data']
        self.assertEqual(datos['tipo'], 'estado_turno')
        self.assertEqual(datos['mensaje'], 'Tu turno fue confirmado.')
        self.assertFalse(datos['leida'])
        self.assertTrue(datos['id'])
        self.assertTrue(datos['fecha_creacion'].endswith('Z'))

    async def test_el_id_coincide_con_el_documento_guardado(self):
        cliente = await sync_to_async(self.crear_cliente)()
        comunicador = await self.conectar_autenticado(cliente.usuario)

        await sync_to_async(registrar_notificacion)(cliente.usuario_id, 'bienvenida', 'Hola')

        mensaje = await comunicador.receive_json_from()
        guardada = self.mongo.notificaciones.docs[0]
        self.assertEqual(mensaje['data']['id'], str(guardada['_id']))

    async def test_no_llega_a_otro_usuario(self):
        uno = await sync_to_async(self.crear_cliente)()
        otro = await sync_to_async(self.crear_cliente)()
        comunicador_otro = await self.conectar_autenticado(otro.usuario)

        await sync_to_async(registrar_notificacion)(uno.usuario_id, 'bienvenida', 'Hola')

        self.assertTrue(await comunicador_otro.receive_nothing(timeout=0.2))

    async def test_varias_pestanias_del_mismo_usuario_reciben_el_aviso(self):
        cliente = await sync_to_async(self.crear_cliente)()
        pestania_a = await self.conectar_autenticado(cliente.usuario)
        pestania_b = await self.conectar_autenticado(cliente.usuario)

        await sync_to_async(registrar_notificacion)(cliente.usuario_id, 'bienvenida', 'Hola')

        self.assertEqual((await pestania_a.receive_json_from())['type'], 'notificacion')
        self.assertEqual((await pestania_b.receive_json_from())['type'], 'notificacion')

    async def test_notificar_a_un_usuario_desconectado_no_falla(self):
        cliente = await sync_to_async(self.crear_cliente)()

        await sync_to_async(registrar_notificacion)(cliente.usuario_id, 'bienvenida', 'Hola')

        self.assertEqual(len(self.mongo.notificaciones.docs), 1)

    async def test_si_la_capa_de_canales_falla_la_notificacion_igual_se_guarda(self):
        cliente = await sync_to_async(self.crear_cliente)()

        with mock.patch('gestion.realtime.get_channel_layer', side_effect=RuntimeError('redis caído')), \
                self.assertLogs('gestion.realtime', level='ERROR'):
            await sync_to_async(registrar_notificacion)(cliente.usuario_id, 'bienvenida', 'Hola')

        self.assertEqual(len(self.mongo.notificaciones.docs), 1)

    async def test_reservar_un_turno_avisa_al_barbero_en_vivo(self):
        esc = await sync_to_async(self.escenario_reservable)()
        comunicador = await self.conectar_autenticado(esc['barbero'].usuario)
        await sync_to_async(self.autenticar)(esc['cliente'].usuario)

        resp = await sync_to_async(self.reservar)(esc)

        self.assertEqual(resp.status_code, 201, resp.data)
        mensaje = await comunicador.receive_json_from()
        self.assertEqual(mensaje['data']['tipo'], 'nuevo_turno')

    async def test_cambiar_el_estado_avisa_al_cliente_en_vivo(self):
        barbero = await sync_to_async(self.crear_barbero)()
        cliente = await sync_to_async(self.crear_cliente)()
        servicio = await sync_to_async(self.crear_servicio)()
        turno = await sync_to_async(self.crear_turno)(cliente, barbero, servicio, hora_inicio=time(12, 0))
        comunicador = await self.conectar_autenticado(cliente.usuario)
        await sync_to_async(self.autenticar)(barbero.usuario)

        resp = await sync_to_async(self.client.patch)(
            reverse('turnos-detail', args=[turno.id]), {'estado': 'confirmado'}, format='json')

        self.assertEqual(resp.status_code, 200, resp.data)
        mensaje = await comunicador.receive_json_from()
        self.assertEqual(mensaje['data']['tipo'], 'estado_turno')
