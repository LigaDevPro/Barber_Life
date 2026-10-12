"""
Notificaciones (Mongo) y Reseñas. Solo los casos importantes.

Las vistas de notificaciones leen la colección directo con pymongo; acá se
reemplaza por `FakeMongoDB` (ver base.py) y se insertan documentos a mano.
"""
from datetime import datetime, timedelta, timezone as dt_timezone

from django.urls import reverse
from django.utils.dateparse import parse_datetime

from gestion.models import Resena, Turno

from .base import BarberLifeTestCase

URL_NOTIFICACIONES = reverse('notificaciones-list')
URL_RESENAS = reverse('resenas-list')


class NotificacionesTests(BarberLifeTestCase):
    def setUp(self):
        super().setUp()
        self.usuario = self.crear_usuario()
        self.autenticar(self.usuario)

    def nueva_notificacion(self, usuario=None, minutos_atras=0, **extra):
        """Inserta un doc en Mongo con fecha naive-UTC, como hace mongo.py."""
        doc = {
            'usuario_id': (usuario or self.usuario).id,
            'tipo': 'prueba',
            'mensaje': 'Mensaje de prueba',
            'canal': 'interna',
            'leida': False,
            'fecha_creacion': datetime.utcnow() - timedelta(minutes=minutos_atras),
        }
        doc.update(extra)
        return self.mongo.notificaciones.insert_one(doc).inserted_id

    def url_leida(self, id_):
        return reverse('notificaciones-leida', kwargs={'id': str(id_)})

    def test_lista_solo_las_propias_mas_nuevas_primero(self):
        self.nueva_notificacion(minutos_atras=30, mensaje='vieja')
        self.nueva_notificacion(minutos_atras=1, mensaje='nueva')
        self.nueva_notificacion(self.crear_usuario(), mensaje='ajena')

        resp = self.client.get(URL_NOTIFICACIONES)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 2)
        self.assertEqual([n['mensaje'] for n in resp.data['results']], ['nueva', 'vieja'])

    def test_paginacion(self):
        for i in range(10):
            self.nueva_notificacion(minutos_atras=i, mensaje=f'n{i}')

        p1 = self.client.get(URL_NOTIFICACIONES).data
        p2 = self.client.get(URL_NOTIFICACIONES, {'page': 2}).data

        self.assertEqual((p1['count'], p1['num_pages'], len(p1['results'])), (10, 2, 7))
        self.assertEqual([n['mensaje'] for n in p2['results']], ['n7', 'n8', 'n9'])

    def test_filtro_leida(self):
        self.nueva_notificacion(leida=True, mensaje='leida')
        self.nueva_notificacion(leida=False, mensaje='nueva')

        for valor, esperado in (('true', ['leida']), ('false', ['nueva'])):
            with self.subTest(leida=valor):
                resp = self.client.get(URL_NOTIFICACIONES, {'leida': valor})
                self.assertEqual([n['mensaje'] for n in resp.data['results']], esperado)

    def test_filtro_leida_invalido_400(self):
        resp = self.client.get(URL_NOTIFICACIONES, {'leida': 'quizas'})

        self.assertEqual(resp.status_code, 400)
        self.assertIn('leida', resp.data)

    def test_fecha_naive_se_serializa_como_utc(self):
        # Bug histórico: un naive se mostraba corrido 3hs (tz Córdoba).
        self.nueva_notificacion(fecha_creacion=datetime(2026, 1, 15, 12, 0, 0))

        fecha = self.client.get(URL_NOTIFICACIONES).data['results'][0]['fecha_creacion']

        # DRF la muestra en hora local (-03:00); lo que importa es el instante.
        self.assertEqual(parse_datetime(fecha), datetime(2026, 1, 15, 12, 0, 0, tzinfo=dt_timezone.utc))

    def test_marcar_leida_persiste_en_mongo(self):
        id_ = self.nueva_notificacion()

        resp = self.client.patch(self.url_leida(id_))

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['leida'])
        self.assertTrue(self.mongo.notificaciones.find_one({'_id': id_})['leida'])

    def test_marcar_leida_ajena_o_inexistente_404(self):
        ajena = self.nueva_notificacion(self.crear_usuario())

        for id_ in (ajena, 'no-es-un-objectid', '0123456789abcdef01234567'):
            with self.subTest(id=id_):
                self.assertEqual(self.client.patch(self.url_leida(id_)).status_code, 404)
        self.assertFalse(self.mongo.notificaciones.find_one({'_id': ajena})['leida'])

    def test_sin_token_401(self):
        id_ = self.nueva_notificacion()
        self.desautenticar()

        self.assertEqual(self.client.get(URL_NOTIFICACIONES).status_code, 401)
        self.assertEqual(self.client.patch(self.url_leida(id_)).status_code, 401)


class ResenasTests(BarberLifeTestCase):
    def setUp(self):
        super().setUp()
        self.cliente = self.crear_cliente()
        self.barbero = self.crear_barbero()
        self.servicio = self.crear_servicio()
        self.turno = self.crear_turno(
            self.cliente, self.barbero, self.servicio, estado=Turno.Estado.COMPLETADO,
        )

    def post(self, **extra):
        payload = {'turno': self.turno.id, 'puntaje': 5, 'comentario': 'Impecable'}
        payload.update(extra)
        return self.client.post(URL_RESENAS, payload, format='json')

    def test_listado_publico_filtrado_por_barbero(self):
        otro = self.crear_barbero()
        otro_turno = self.crear_turno(
            self.cliente, otro, self.servicio, hora_inicio=self.turno.hora_inicio,
            estado=Turno.Estado.COMPLETADO,
        )
        Resena.objects.create(turno=self.turno, cliente=self.cliente, barbero=self.barbero, puntaje=5)
        Resena.objects.create(turno=otro_turno, cliente=self.cliente, barbero=otro, puntaje=2)

        resp = self.client.get(URL_RESENAS, {'barbero': self.barbero.id})  # sin token

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['barbero'], self.barbero.id)

    def test_cliente_dueno_crea_resena_y_datos_salen_del_turno(self):
        otro_barbero = self.crear_barbero()
        self.autenticar(self.cliente.usuario)

        # barbero/cliente del body se ignoran: salen del turno.
        resp = self.post(barbero=otro_barbero.id)

        self.assertEqual(resp.status_code, 201)
        resena = Resena.objects.get(turno=self.turno)
        self.assertEqual((resena.cliente, resena.barbero, resena.puntaje), (self.cliente, self.barbero, 5))
        self.assertEqual(len(self.eventos_log('creacion_resena')), 1)

    def test_turno_no_completado_400(self):
        self.autenticar(self.cliente.usuario)

        for estado in (Turno.Estado.PENDIENTE, Turno.Estado.CONFIRMADO, Turno.Estado.CANCELADO):
            with self.subTest(estado=estado):
                self.turno.estado = estado
                self.turno.save(update_fields=['estado'])
                self.assertEqual(self.post().status_code, 400)
        self.assertFalse(Resena.objects.exists())

    def test_puntaje_fuera_de_rango_400(self):
        self.autenticar(self.cliente.usuario)

        for valor in (0, 6):
            with self.subTest(puntaje=valor):
                resp = self.post(puntaje=valor)
                self.assertEqual(resp.status_code, 400)
                self.assertIn('puntaje', resp.data)

    def test_segunda_resena_al_mismo_turno_400_no_500(self):
        self.autenticar(self.cliente.usuario)
        self.assertEqual(self.post().status_code, 201)

        resp = self.post(puntaje=1)

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Resena.objects.get(turno=self.turno).puntaje, 5)

    def test_turno_ajeno_o_barbero_403_y_sin_token_401(self):
        for usuario, esperado in (
            (self.crear_cliente().usuario, 403),
            (self.barbero.usuario, 403),
            (None, 401),
        ):
            with self.subTest(esperado=esperado, rol=getattr(usuario, 'rol', None)):
                self.desautenticar()
                if usuario:
                    self.autenticar(usuario)
                self.assertEqual(self.post().status_code, esperado)
        self.assertFalse(Resena.objects.exists())
