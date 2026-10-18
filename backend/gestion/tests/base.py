"""
Infraestructura común de los tests del backend.

Todos los tests de `gestion/tests/` heredan de `BarberLifeTestCase`, que:

* reemplaza MongoDB por una base en memoria (`FakeMongoDB`) — los tests no
  necesitan un Mongo corriendo y pueden inspeccionar qué se registró;
* reemplaza las llamadas a Mercado Pago (`crear_preferencia`/`obtener_pago`)
  por mocks configurables — nunca se pega a la API real;
* ofrece fábricas (`crear_cliente`, `crear_turno`, ...) y `autenticar()` para
  loguear un request con un JWT real (el `RoleCheckMiddleware` valida el
  token, así que `force_authenticate` no alcanza).

Se corre con:  python manage.py test gestion
"""
from datetime import date, time, timedelta
from itertools import count
from unittest import mock

from bson import ObjectId
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from gestion.models import (
    Usuario, Cliente, Barbero, Servicio, Horario, BarberoServicio, Turno, Pago,
)

_seq = count(1)


# ---------------------------------------------------------------------------
# Mongo en memoria
# ---------------------------------------------------------------------------

class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, campo, direccion=1):
        self._docs.sort(key=lambda d: d.get(campo), reverse=direccion < 0)
        return self

    def skip(self, n):
        self._docs = self._docs[n:]
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    def __iter__(self):
        return iter(self._docs)


class FakeCollection:
    """Subconjunto de la API de pymongo que usa el proyecto: insert_one,
    find, find_one, count_documents y update_one con `$set`. Los filtros
    son solo igualdad por campo (alcanza para las vistas actuales)."""

    def __init__(self):
        self.docs = []

    @staticmethod
    def _coincide(doc, filtro):
        return all(doc.get(k) == v for k, v in (filtro or {}).items())

    def insert_one(self, doc):
        doc = dict(doc)
        doc.setdefault('_id', ObjectId())
        self.docs.append(doc)
        return mock.Mock(inserted_id=doc['_id'])

    def find(self, filtro=None):
        return _FakeCursor(d for d in self.docs if self._coincide(d, filtro))

    def find_one(self, filtro=None):
        return next((d for d in self.docs if self._coincide(d, filtro)), None)

    def count_documents(self, filtro=None):
        return sum(1 for d in self.docs if self._coincide(d, filtro))

    def update_one(self, filtro, cambios):
        doc = self.find_one(filtro)
        if doc is not None:
            doc.update(cambios.get('$set', {}))

    def clear(self):
        self.docs.clear()


class FakeMongoDB:
    """Reemplazo de `get_mongo_db()`: colecciones creadas a demanda."""

    def __init__(self):
        self._colecciones = {}

    def __getattr__(self, nombre):
        if nombre.startswith('_'):
            raise AttributeError(nombre)
        return self._colecciones.setdefault(nombre, FakeCollection())

    def __getitem__(self, nombre):
        return getattr(self, nombre)


# ---------------------------------------------------------------------------
# Caso base
# ---------------------------------------------------------------------------

class BarberLifeTestCase(APITestCase):
    PASSWORD = 'Clave-de-prueba-123'

    def setUp(self):
        super().setUp()
        self.mongo = FakeMongoDB()
        for destino in ('gestion.mongo.get_mongo_db', 'gestion.views.notificacion.get_mongo_db'):
            patcher = mock.patch(destino, return_value=self.mongo)
            patcher.start()
            self.addCleanup(patcher.stop)

        # Mercado Pago: por defecto "responde bien". Cada test puede pisar
        # `.return_value` / `.side_effect` para simular otros escenarios.
        self.mp_crear_preferencia = self._patch(
            'gestion.views.pago.crear_preferencia',
            return_value={'id': 'pref-test-123', 'init_point': 'https://mp.test/checkout/pref-test-123'},
        )
        self.mp_obtener_pago = self._patch('gestion.views.pago.obtener_pago')

    def _patch(self, destino, **kwargs):
        patcher = mock.patch(destino, **kwargs)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    # -- autenticación ------------------------------------------------------

    def autenticar(self, usuario):
        """Los requests siguientes del `self.client` van con un JWT real."""
        token = RefreshToken.for_user(usuario).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return usuario

    def desautenticar(self):
        self.client.credentials()

    # -- fábricas -----------------------------------------------------------

    def crear_usuario(self, rol=Usuario.Rol.CLIENTE, **extra):
        n = next(_seq)
        email = extra.pop('email', f'{rol}{n}@test.com')
        extra.setdefault('first_name', rol.capitalize())
        extra.setdefault('last_name', f'Test{n}')
        return Usuario.objects.create_user(
            username=email, email=email, password=self.PASSWORD, rol=rol, **extra,
        )

    def crear_admin(self, **extra):
        return self.crear_usuario(Usuario.Rol.ADMIN, **extra)

    def crear_cliente(self, **extra):
        usuario = self.crear_usuario(Usuario.Rol.CLIENTE, **extra)
        return Cliente.objects.create(usuario=usuario)

    def crear_barbero(self, activo=True, **extra):
        usuario = self.crear_usuario(Usuario.Rol.BARBERO, **extra)
        return Barbero.objects.create(usuario=usuario, activo=activo)

    def crear_servicio(self, nombre=None, duracion_minutos=30, precio='5000.00', activo=True):
        return Servicio.objects.create(
            nombre=nombre or f'Servicio {next(_seq)}',
            duracion_minutos=duracion_minutos, precio=precio, activo=activo,
        )

    def crear_horario(self, barbero, dia_semana=1, hora_inicio=time(9, 0), hora_fin=time(18, 0),
                      intervalo_minutos=30, activo=True):
        return Horario.objects.create(
            barbero=barbero, dia_semana=dia_semana, hora_inicio=hora_inicio,
            hora_fin=hora_fin, intervalo_minutos=intervalo_minutos, activo=activo,
        )

    def crear_oferta(self, barbero, servicio, horario, precio_personalizado=None, activo=True):
        return BarberoServicio.objects.create(
            barbero=barbero, servicio=servicio, horario=horario,
            precio_personalizado=precio_personalizado, activo=activo,
        )

    def crear_turno(self, cliente, barbero, servicio, fecha_turno=None, hora_inicio=time(10, 0),
                    estado=Turno.Estado.PENDIENTE):
        """Crea un turno directo en la base (sin pasar por la API ni sus
        validaciones). `hora_fin` se calcula con la duración del servicio."""
        fecha_turno = fecha_turno or self.fecha_futura()
        inicio = timedelta(hours=hora_inicio.hour, minutes=hora_inicio.minute)
        fin = inicio + timedelta(minutes=servicio.duracion_minutos)
        hora_fin = time(fin.seconds // 3600, (fin.seconds % 3600) // 60)
        return Turno.objects.create(
            cliente=cliente, barbero=barbero, servicio=servicio,
            fecha_turno=fecha_turno, hora_inicio=hora_inicio, hora_fin=hora_fin, estado=estado,
        )

    def crear_pago(self, turno, estado=Pago.Estado.PENDIENTE, **extra):
        extra.setdefault('monto_total', turno.precio())
        return Pago.objects.create(turno=turno, estado=estado, **extra)

    def escenario_reservable(self, dia_semana=None):
        """Todo lo necesario para reservar un turno válido: barbero con un
        horario activo (lun-dom según `dia_semana`, por defecto el de la
        próxima semana) y un servicio ofrecido en él. Devuelve un dict."""
        fecha = self.fecha_futura(dia_semana=dia_semana)
        cliente = self.crear_cliente()
        barbero = self.crear_barbero()
        servicio = self.crear_servicio()
        horario = self.crear_horario(barbero, dia_semana=fecha.isoweekday())
        oferta = self.crear_oferta(barbero, servicio, horario)
        return {
            'cliente': cliente, 'barbero': barbero, 'servicio': servicio,
            'horario': horario, 'oferta': oferta, 'fecha': fecha,
        }

    # -- fechas -------------------------------------------------------------

    @staticmethod
    def fecha_futura(dia_semana=None, dias_minimos=7):
        """Primera fecha a `dias_minimos` días o más de hoy. Con
        `dia_semana` (1=lunes ... 7=domingo) devuelve la primera que caiga
        en ese día; sin él, simplemente hoy + `dias_minimos`."""
        fecha = date.today() + timedelta(days=dias_minimos)
        if dia_semana is not None:
            while fecha.isoweekday() != dia_semana:
                fecha += timedelta(days=1)
        return fecha

    # -- aserciones útiles --------------------------------------------------

    def notificaciones_de(self, usuario, tipo=None):
        return [
            d for d in self.mongo.notificaciones.docs
            if d['usuario_id'] == usuario.id and (tipo is None or d['tipo'] == tipo)
        ]

    def eventos_log(self, accion=None):
        return [d for d in self.mongo.eventos_log.docs if accion is None or d['accion'] == accion]
