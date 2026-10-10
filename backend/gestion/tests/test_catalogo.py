"""
Catálogo y disponibilidad: Servicio, Horario, BarberoServicio.

Foco en lo importante: visibilidad pública vs privada, permisos por rol,
ownership del barbero, soft delete y las validaciones de negocio clave.

Se corre con:  python manage.py test gestion.tests.test_catalogo
"""
import unittest

from django.urls import reverse

from gestion.models import Servicio, Horario, BarberoServicio

from .base import BarberLifeTestCase


class CatalogoTestCase(BarberLifeTestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.crear_admin()
        self.cliente = self.crear_cliente()
        self.barbero = self.crear_barbero()
        self.otro_barbero = self.crear_barbero()


class ServicioTests(CatalogoTestCase):
    def setUp(self):
        super().setUp()
        self.activo = self.crear_servicio('Corte', precio='8000.00')
        self.inactivo = self.crear_servicio('Viejo', activo=False)
        self.url_lista = reverse('servicios-list')

    def _url_detalle(self, servicio):
        return reverse('servicios-detail', args=[servicio.id])

    def test_listado_publico_solo_muestra_activos_y_admin_ve_todos(self):
        ids = [s['id'] for s in self.client.get(self.url_lista).data]
        self.assertIn(self.activo.id, ids)
        self.assertNotIn(self.inactivo.id, ids)

        self.autenticar(self.admin)
        ids_admin = [s['id'] for s in self.client.get(self.url_lista).data]
        self.assertIn(self.inactivo.id, ids_admin)

    def test_detalle_de_inactivo_404_para_no_admin_y_visible_para_admin(self):
        self.assertEqual(self.client.get(self._url_detalle(self.inactivo)).status_code, 404)
        self.autenticar(self.admin)
        self.assertEqual(self.client.get(self._url_detalle(self.inactivo)).status_code, 200)

    def test_alta_edicion_y_baja_solo_admin(self):
        datos = {'nombre': 'Barba', 'duracion_minutos': 20, 'precio': '3500.00'}
        for usuario in (self.cliente.usuario, self.barbero.usuario):
            self.autenticar(usuario)
            self.assertEqual(self.client.post(self.url_lista, datos, format='json').status_code, 403)
            self.assertEqual(
                self.client.patch(self._url_detalle(self.activo), {'precio': '1.00'}, format='json').status_code, 403,
            )
            self.assertEqual(self.client.delete(self._url_detalle(self.activo)).status_code, 403)
        self.activo.refresh_from_db()
        self.assertEqual(str(self.activo.precio), '8000.00')
        self.assertTrue(self.activo.activo)
        self.assertFalse(Servicio.objects.filter(nombre='Barba').exists())

        self.autenticar(self.admin)
        self.assertEqual(self.client.post(self.url_lista, datos, format='json').status_code, 201)
        resp = self.client.patch(self._url_detalle(self.activo), {'precio': '9500.00'}, format='json')
        self.assertEqual(resp.status_code, 200)

    def test_delete_es_soft_delete_aun_con_turnos_asociados(self):
        # Turno.servicio es PROTECT: un borrado real fallaría.
        horario = self.crear_horario(self.barbero)
        self.crear_oferta(self.barbero, self.activo, horario)
        self.crear_turno(self.cliente, self.barbero, self.activo)
        self.autenticar(self.admin)

        resp = self.client.delete(self._url_detalle(self.activo))

        self.assertEqual(resp.status_code, 204)
        self.activo.refresh_from_db()
        self.assertFalse(self.activo.activo)

    @unittest.expectedFailure
    def test_precio_negativo_deberia_rechazarse(self):
        # BUG: ni el modelo ni el serializer validan precio >= 0.
        self.autenticar(self.admin)

        resp = self.client.post(
            self.url_lista, {'nombre': 'Gratis', 'duracion_minutos': 10, 'precio': '-100.00'}, format='json',
        )

        self.assertEqual(resp.status_code, 400)


class HorarioTests(CatalogoTestCase):
    def setUp(self):
        super().setUp()
        self.horario = self.crear_horario(self.barbero, dia_semana=2)
        self.horario_ajeno = self.crear_horario(self.otro_barbero, dia_semana=3)
        self.url_lista = reverse('horarios-list')

    def _url_detalle(self, horario):
        return reverse('horarios-detail', args=[horario.id])

    def _datos(self, **extra):
        datos = {'dia_semana': 5, 'hora_inicio': '10:00', 'hora_fin': '14:00', 'intervalo_minutos': 30}
        datos.update(extra)
        return datos

    def test_barbero_solo_ve_los_suyos_aunque_manipule_el_query_param(self):
        self.autenticar(self.barbero.usuario)

        resp = self.client.get(self.url_lista, {'barbero': self.otro_barbero.id})

        self.assertEqual([h['id'] for h in resp.data], [self.horario.id])

    def test_admin_ve_todos_y_filtra_por_barbero(self):
        self.autenticar(self.admin)

        todos = [h['id'] for h in self.client.get(self.url_lista).data]
        filtrados = [h['id'] for h in self.client.get(self.url_lista, {'barbero': self.otro_barbero.id}).data]

        self.assertCountEqual(todos, [self.horario.id, self.horario_ajeno.id])
        self.assertEqual(filtrados, [self.horario_ajeno.id])

    def test_cliente_y_anonimo_no_acceden(self):
        self.assertEqual(self.client.get(self.url_lista).status_code, 401)
        self.autenticar(self.cliente.usuario)
        self.assertEqual(self.client.get(self.url_lista).status_code, 403)
        self.assertEqual(self.client.post(self.url_lista, self._datos(), format='json').status_code, 403)

    def test_barbero_crea_para_si_e_ignora_el_barbero_del_body(self):
        self.autenticar(self.barbero.usuario)

        resp = self.client.post(self.url_lista, self._datos(barbero=self.otro_barbero.id), format='json')

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Horario.objects.get(pk=resp.data['id']).barbero_id, self.barbero.id)

    def test_admin_elige_barbero_y_sin_barbero_es_400(self):
        self.autenticar(self.admin)

        resp = self.client.post(self.url_lista, self._datos(barbero=self.otro_barbero.id), format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Horario.objects.get(pk=resp.data['id']).barbero_id, self.otro_barbero.id)

        resp = self.client.post(self.url_lista, self._datos(), format='json')
        self.assertEqual(resp.status_code, 400)

    def test_barbero_no_accede_ni_modifica_horario_ajeno(self):
        self.autenticar(self.barbero.usuario)
        url = self._url_detalle(self.horario_ajeno)

        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.patch(url, {'hora_fin': '20:00'}, format='json').status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.horario_ajeno.refresh_from_db()
        self.assertTrue(self.horario_ajeno.activo)

    def test_delete_es_soft_delete_y_conserva_las_ofertas(self):
        # Un borrado real arrastraría BarberoServicio por CASCADE.
        oferta = self.crear_oferta(self.barbero, self.crear_servicio(), self.horario)
        self.autenticar(self.barbero.usuario)

        resp = self.client.delete(self._url_detalle(self.horario))

        self.assertEqual(resp.status_code, 204)
        self.horario.refresh_from_db()
        self.assertFalse(self.horario.activo)
        self.assertTrue(BarberoServicio.objects.filter(pk=oferta.pk).exists())

    @unittest.expectedFailure
    def test_hora_fin_menor_o_igual_a_hora_inicio_deberia_rechazarse(self):
        # BUG: no hay validación de hora_fin > hora_inicio ni en modelo ni serializer.
        self.autenticar(self.barbero.usuario)

        resp = self.client.post(
            self.url_lista, self._datos(hora_inicio='18:00', hora_fin='09:00'), format='json',
        )

        self.assertEqual(resp.status_code, 400)


class BarberoServicioTests(CatalogoTestCase):
    def setUp(self):
        super().setUp()
        self.servicio = self.crear_servicio('Corte', precio='8000.00')
        self.horario = self.crear_horario(self.barbero)
        self.horario_ajeno = self.crear_horario(self.otro_barbero)
        self.oferta = self.crear_oferta(self.barbero, self.servicio, self.horario)
        self.oferta_ajena = self.crear_oferta(self.otro_barbero, self.servicio, self.horario_ajeno)
        self.url_lista = reverse('barbero-servicio-list')

    def _url_detalle(self, oferta):
        return reverse('barbero-servicio-detail', args=[oferta.id])

    def test_listado_publico_solo_activos(self):
        inactiva = self.crear_oferta(self.barbero, self.crear_servicio(), self.horario, activo=False)

        ids = [o['id'] for o in self.client.get(self.url_lista).data]

        self.assertCountEqual(ids, [self.oferta.id, self.oferta_ajena.id])
        self.assertNotIn(inactiva.id, ids)

    def test_barbero_arma_su_oferta(self):
        servicio = self.crear_servicio()
        horario = self.crear_horario(self.barbero, dia_semana=4)
        self.autenticar(self.barbero.usuario)

        resp = self.client.post(
            self.url_lista, {'servicio': servicio.id, 'horario': horario.id}, format='json',
        )

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(BarberoServicio.objects.get(pk=resp.data['id']).barbero_id, self.barbero.id)

    def test_horario_de_otro_barbero_es_400_para_barbero_y_admin(self):
        servicio = self.crear_servicio()
        self.autenticar(self.barbero.usuario)
        resp = self.client.post(
            self.url_lista, {'servicio': servicio.id, 'horario': self.horario_ajeno.id}, format='json',
        )
        self.assertEqual(resp.status_code, 400)

        self.autenticar(self.admin)
        resp = self.client.post(
            self.url_lista,
            {'barbero': self.barbero.id, 'servicio': servicio.id, 'horario': self.horario_ajeno.id},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_oferta_duplicada_es_400(self):
        self.autenticar(self.barbero.usuario)

        resp = self.client.post(
            self.url_lista, {'servicio': self.servicio.id, 'horario': self.horario.id}, format='json',
        )

        self.assertEqual(resp.status_code, 400)

    def test_cliente_y_anonimo_no_pueden_escribir(self):
        datos = {'servicio': self.servicio.id, 'horario': self.horario.id}
        self.assertEqual(self.client.post(self.url_lista, datos, format='json').status_code, 401)
        self.autenticar(self.cliente.usuario)
        self.assertEqual(self.client.post(self.url_lista, datos, format='json').status_code, 403)
        self.assertEqual(self.client.delete(self._url_detalle(self.oferta)).status_code, 403)

    def test_solo_dueno_o_admin_editan_y_borran(self):
        url_ajena = self._url_detalle(self.oferta_ajena)
        self.autenticar(self.barbero.usuario)

        self.assertEqual(
            self.client.patch(url_ajena, {'precio_personalizado': '1.00'}, format='json').status_code, 403,
        )
        self.assertEqual(self.client.delete(url_ajena).status_code, 403)
        self.oferta_ajena.refresh_from_db()
        self.assertIsNone(self.oferta_ajena.precio_personalizado)
        self.assertTrue(self.oferta_ajena.activo)

        resp = self.client.patch(
            self._url_detalle(self.oferta), {'precio_personalizado': '6000.00'}, format='json',
        )
        self.assertEqual(resp.status_code, 200)

        self.autenticar(self.admin)
        self.assertEqual(self.client.delete(url_ajena).status_code, 204)

    def test_delete_es_soft_delete(self):
        self.autenticar(self.barbero.usuario)

        resp = self.client.delete(self._url_detalle(self.oferta))

        self.assertEqual(resp.status_code, 204)
        self.oferta.refresh_from_db()
        self.assertFalse(self.oferta.activo)
        ids = [o['id'] for o in self.client.get(self.url_lista).data]
        self.assertNotIn(self.oferta.id, ids)

    def test_patch_no_deberia_permitir_reasignar_la_oferta_a_otro_barbero(self):
        # `barbero` no se puede reasignar en el PATCH (autorización).
        self.autenticar(self.barbero.usuario)

        resp = self.client.patch(
            self._url_detalle(self.oferta), {'barbero': self.otro_barbero.id}, format='json',
        )

        self.assertIn(resp.status_code, (400, 403))
        self.oferta.refresh_from_db()
        self.assertEqual(self.oferta.barbero_id, self.barbero.id)

    def test_patch_legitimo_con_su_propio_barbero_y_horario_funciona(self):
        # El fix no debe bloquear ediciones válidas: reenviar el mismo
        # `barbero` o moverse a otro horario PROPIO sigue siendo 200.
        self.autenticar(self.barbero.usuario)
        otro_horario_propio = self.crear_horario(self.barbero, dia_semana=3)

        resp = self.client.patch(
            self._url_detalle(self.oferta),
            {'barbero': self.barbero.id, 'horario': otro_horario_propio.id},
            format='json',
        )

        self.assertEqual(resp.status_code, 200)
        self.oferta.refresh_from_db()
        self.assertEqual(self.oferta.horario_id, otro_horario_propio.id)

    def test_patch_no_deberia_permitir_cambiar_a_horario_de_otro_barbero(self):
        # La validación "el horario pertenece al barbero" aplica también al PATCH.
        self.autenticar(self.barbero.usuario)

        resp = self.client.patch(
            self._url_detalle(self.oferta), {'horario': self.horario_ajeno.id}, format='json',
        )

        self.assertEqual(resp.status_code, 400)