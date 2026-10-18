"""
Búsqueda con filtros combinados (texto + rango de fechas + estado) y
exportación a CSV de los turnos.

Cubre FiltrosTurnosMixin, TurnosListView y TurnosExportarView (views/turno.py).
"""
import csv
import io
from datetime import date, time

from django.urls import reverse

from gestion.models import Turno

from .base import BarberLifeTestCase


class FiltrosYExportacionBase(BarberLifeTestCase):
    def setUp(self):
        super().setUp()
        self.barbero = self.crear_barbero()
        self.otro_barbero = self.crear_barbero()
        self.servicio = self.crear_servicio(nombre='Corte de pelo', precio='15.00')
        self.juan = self.crear_cliente(first_name='Juan', last_name='Pérez', email='juan.perez@test.com')
        self.ana = self.crear_cliente(first_name='Ana', last_name='Gómez', email='ana.gomez@test.com')

        self.t1 = self.crear_turno(self.juan, self.barbero, self.servicio, date(2026, 10, 10),
                                   estado=Turno.Estado.PENDIENTE)
        self.t2 = self.crear_turno(self.juan, self.barbero, self.servicio, date(2026, 10, 15),
                                   estado=Turno.Estado.CONFIRMADO)
        self.t3 = self.crear_turno(self.ana, self.barbero, self.servicio, date(2026, 10, 20),
                                   estado=Turno.Estado.CONFIRMADO)
        self.t_ajeno = self.crear_turno(self.ana, self.otro_barbero, self.servicio, date(2026, 10, 15))

    def ids(self, resp):
        return {t['id'] for t in resp.data['results']}


class FiltroPorRangoDeFechasTests(FiltrosYExportacionBase):
    def listar(self, **params):
        return self.client.get(reverse('turnos-list'), params)

    def test_fecha_desde_y_hasta_son_inclusivas(self):
        self.autenticar(self.barbero.usuario)

        resp = self.listar(fecha_desde='2026-10-15', fecha_hasta='2026-10-20')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.ids(resp), {self.t2.id, self.t3.id})

    def test_solo_fecha_desde(self):
        self.autenticar(self.barbero.usuario)

        resp = self.listar(fecha_desde='2026-10-16')

        self.assertEqual(self.ids(resp), {self.t3.id})

    def test_solo_fecha_hasta(self):
        self.autenticar(self.barbero.usuario)

        resp = self.listar(fecha_hasta='2026-10-10')

        self.assertEqual(self.ids(resp), {self.t1.id})

    def test_combina_texto_rango_y_estado(self):
        self.autenticar(self.barbero.usuario)

        resp = self.listar(q='Juan', estado='confirmado',
                           fecha_desde='2026-10-01', fecha_hasta='2026-10-31')

        self.assertEqual(self.ids(resp), {self.t2.id})

    def test_barbero_no_ve_turnos_ajenos_aunque_el_rango_los_incluya(self):
        self.autenticar(self.barbero.usuario)

        resp = self.listar(fecha_desde='2026-10-15', fecha_hasta='2026-10-15', barbero=self.otro_barbero.id)

        self.assertEqual(self.ids(resp), {self.t2.id})

    def test_admin_filtra_por_barbero_y_rango(self):
        admin = self.crear_admin()
        self.autenticar(admin)

        resp = self.listar(barbero=self.otro_barbero.id, fecha_desde='2026-10-01')

        self.assertEqual(self.ids(resp), {self.t_ajeno.id})

    def test_fecha_con_formato_invalido_devuelve_400(self):
        self.autenticar(self.barbero.usuario)

        resp = self.listar(fecha_desde='15/10/2026')

        self.assertEqual(resp.status_code, 400)
        self.assertIn('fecha_desde', resp.data)

    def test_rango_invertido_devuelve_400(self):
        self.autenticar(self.barbero.usuario)

        resp = self.listar(fecha_desde='2026-10-20', fecha_hasta='2026-10-10')

        self.assertEqual(resp.status_code, 400)
        self.assertIn('fecha_hasta', resp.data)


class ExportarTurnosCsvTests(FiltrosYExportacionBase):
    def exportar(self, **params):
        return self.client.get(reverse('turnos-exportar'), params)

    def filas(self, resp):
        texto = resp.content.decode('utf-8-sig')
        return list(csv.reader(io.StringIO(texto)))

    def test_exporta_csv_con_encabezado_y_una_fila_por_turno(self):
        self.autenticar(self.barbero.usuario)

        resp = self.exportar()

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp['Content-Type'].startswith('text/csv'))
        self.assertIn('attachment; filename="turnos.csv"', resp['Content-Disposition'])
        filas = self.filas(resp)
        self.assertEqual(filas[0][:3], ['ID', 'Fecha', 'Hora inicio'])
        self.assertEqual(len(filas), 1 + 3)  # solo los 3 turnos de este barbero

    def test_respeta_los_mismos_filtros_que_el_listado(self):
        self.autenticar(self.barbero.usuario)
        params = dict(estado='confirmado', fecha_desde='2026-10-12', fecha_hasta='2026-10-31')

        listado = self.client.get(reverse('turnos-list'), params)
        csv_resp = self.exportar(**params)

        ids_csv = {int(f[0]) for f in self.filas(csv_resp)[1:]}
        self.assertEqual(ids_csv, self.ids(listado))
        self.assertEqual(ids_csv, {self.t2.id, self.t3.id})

    def test_barbero_solo_exporta_su_agenda(self):
        self.autenticar(self.barbero.usuario)

        resp = self.exportar(barbero=self.otro_barbero.id)

        ids_csv = {int(f[0]) for f in self.filas(resp)[1:]}
        self.assertNotIn(self.t_ajeno.id, ids_csv)

    def test_admin_exporta_todo_y_puede_filtrar_por_barbero(self):
        self.autenticar(self.crear_admin())

        todo = self.filas(self.exportar())
        solo_otro = self.filas(self.exportar(barbero=self.otro_barbero.id))

        self.assertEqual(len(todo), 1 + 4)
        self.assertEqual(len(solo_otro), 1 + 1)

    def test_contenido_de_las_celdas(self):
        self.autenticar(self.barbero.usuario)

        fila = self.filas(self.exportar(fecha_desde='2026-10-10', fecha_hasta='2026-10-10'))[1]

        self.assertEqual(fila[0], str(self.t1.id))
        self.assertEqual(fila[1], '10/10/2026')
        self.assertEqual(fila[2], '10:00')
        self.assertEqual(fila[4], 'Juan Pérez')
        self.assertEqual(fila[5], 'juan.perez@test.com')
        self.assertEqual(fila[7], 'Corte de pelo')
        self.assertEqual(fila[8], 'Pendiente')

    def test_neutraliza_formulas_en_observaciones(self):
        self.t1.observaciones = '=HYPERLINK("http://malo.test","click")'
        self.t1.save()
        self.autenticar(self.barbero.usuario)

        fila = self.filas(self.exportar(fecha_desde='2026-10-10', fecha_hasta='2026-10-10'))[1]

        self.assertTrue(fila[10].startswith("'="))

    def test_registra_el_evento_en_el_log(self):
        self.autenticar(self.barbero.usuario)

        self.exportar()

        self.assertEqual(len(self.eventos_log('exportacion_turnos')), 1)

    def test_cliente_no_puede_exportar(self):
        self.autenticar(self.juan.usuario)

        self.assertEqual(self.exportar().status_code, 403)

    def test_sin_token_devuelve_401(self):
        self.assertEqual(self.exportar().status_code, 401)

    def test_fecha_invalida_devuelve_400(self):
        self.autenticar(self.barbero.usuario)

        self.assertEqual(self.exportar(fecha_hasta='mañana').status_code, 400)
