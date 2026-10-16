"""
Carga de imágenes: foto de perfil del barbero (POST/DELETE /api/barberos/me/foto/).

Los archivos se guardan en un MEDIA_ROOT temporal que se borra al terminar.
"""
import os
import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image

from .base import BarberLifeTestCase


def imagen(formato='PNG', nombre='foto.png', tamanio=(40, 40)):
    buffer = BytesIO()
    Image.new('RGB', tamanio, (200, 30, 30)).save(buffer, formato)
    tipo = {'PNG': 'image/png', 'JPEG': 'image/jpeg', 'WEBP': 'image/webp', 'GIF': 'image/gif'}[formato]
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type=tipo)


class FotoPerfilBase(BarberLifeTestCase):
    def setUp(self):
        super().setUp()
        self.media = tempfile.mkdtemp()
        configuracion = override_settings(MEDIA_ROOT=self.media, BACKEND_PUBLIC_URL='')
        configuracion.enable()
        self.addCleanup(configuracion.disable)
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        self.barbero = self.crear_barbero()
        self.url = reverse('barberos-me-foto')

    def subir(self, archivo):
        return self.client.post(self.url, {'foto': archivo}, format='multipart')


class SubirFotoTests(FotoPerfilBase):
    def test_barbero_sube_una_foto_valida(self):
        self.autenticar(self.barbero.usuario)

        resp = self.subir(imagen('PNG'))

        self.assertEqual(resp.status_code, 201, resp.data)
        self.barbero.refresh_from_db()
        self.assertTrue(self.barbero.foto_perfil)
        self.assertTrue(os.path.exists(self.barbero.foto_perfil.path))
        self.assertTrue(resp.data['foto_perfil_url'].startswith('http://testserver/media/barberos/'))
        self.assertEqual(resp.data['foto_perfil_url'], self.barbero.foto_perfil_url)
        self.assertEqual(len(self.eventos_log('subida_foto_perfil')), 1)

    def test_acepta_jpeg_y_webp(self):
        self.autenticar(self.barbero.usuario)

        self.assertEqual(self.subir(imagen('JPEG', 'a.jpg')).status_code, 201)
        self.assertEqual(self.subir(imagen('WEBP', 'a.webp')).status_code, 201)

    def test_ignora_el_nombre_que_manda_el_cliente(self):
        self.autenticar(self.barbero.usuario)

        self.subir(imagen('PNG', '../../etc/passwd.png'))

        self.barbero.refresh_from_db()
        nombre = os.path.basename(self.barbero.foto_perfil.name)
        self.assertNotIn('passwd', nombre)
        self.assertTrue(nombre.endswith('.png'))
        self.assertTrue(self.barbero.foto_perfil.path.startswith(self.media))

    def test_reemplazar_borra_el_archivo_anterior(self):
        self.autenticar(self.barbero.usuario)
        self.subir(imagen('PNG'))
        self.barbero.refresh_from_db()
        anterior = self.barbero.foto_perfil.path

        self.subir(imagen('JPEG', 'b.jpg'))

        self.barbero.refresh_from_db()
        self.assertFalse(os.path.exists(anterior))
        self.assertTrue(os.path.exists(self.barbero.foto_perfil.path))

    def test_la_foto_se_ve_en_el_listado_publico_y_se_sirve(self):
        self.autenticar(self.barbero.usuario)
        resp = self.subir(imagen('PNG'))
        self.desautenticar()

        listado = self.client.get(reverse('barberos-list')).data
        url = next(b['foto_perfil_url'] for b in listado if b['id'] == self.barbero.id)
        archivo = self.client.get(url.replace('http://testserver', ''))

        self.assertEqual(url, resp.data['foto_perfil_url'])
        self.assertEqual(archivo.status_code, 200)
        self.assertEqual(archivo['Content-Type'], 'image/png')

    @override_settings(BACKEND_PUBLIC_URL='https://api.barberlife.test')
    def test_usa_la_url_publica_configurada(self):
        self.autenticar(self.barbero.usuario)

        resp = self.subir(imagen('PNG'))

        self.assertTrue(resp.data['foto_perfil_url'].startswith('https://api.barberlife.test/media/barberos/'))


class ValidacionFotoTests(FotoPerfilBase):
    def setUp(self):
        super().setUp()
        self.autenticar(self.barbero.usuario)

    def assert_rechazada(self, resp):
        self.assertEqual(resp.status_code, 400, resp.data)
        self.barbero.refresh_from_db()
        self.assertFalse(self.barbero.foto_perfil)
        self.assertEqual(os.listdir(self.media), [])

    def test_rechaza_un_archivo_que_no_es_imagen(self):
        falso = SimpleUploadedFile('foto.png', b'esto no es una imagen', content_type='image/png')

        self.assert_rechazada(self.subir(falso))

    def test_rechaza_formatos_no_permitidos(self):
        self.assert_rechazada(self.subir(imagen('GIF', 'a.gif')))

    def test_rechaza_un_svg_aunque_diga_ser_imagen(self):
        svg = SimpleUploadedFile('x.svg', b'<svg xmlns="http://www.w3.org/2000/svg"></svg>', content_type='image/svg+xml')

        self.assert_rechazada(self.subir(svg))

    @override_settings(FOTO_PERFIL_MAX_BYTES=1000)
    def test_rechaza_imagenes_demasiado_pesadas(self):
        grande = imagen('PNG', tamanio=(400, 400))
        self.assertGreater(grande.size, 1000)

        resp = self.subir(grande)

        self.assert_rechazada(resp)
        self.assertIn('foto', resp.data)

    def test_rechaza_si_falta_el_campo(self):
        resp = self.client.post(self.url, {}, format='multipart')

        self.assertEqual(resp.status_code, 400)


class QuitarFotoTests(FotoPerfilBase):
    def test_quitar_borra_el_archivo_y_la_url(self):
        self.autenticar(self.barbero.usuario)
        self.subir(imagen('PNG'))
        self.barbero.refresh_from_db()
        ruta = self.barbero.foto_perfil.path

        resp = self.client.delete(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['foto_perfil_url'], '')
        self.assertFalse(os.path.exists(ruta))
        self.barbero.refresh_from_db()
        self.assertFalse(self.barbero.foto_perfil)
        self.assertEqual(len(self.eventos_log('baja_foto_perfil')), 1)

    def test_quitar_sin_foto_no_falla(self):
        self.autenticar(self.barbero.usuario)

        self.assertEqual(self.client.delete(self.url).status_code, 200)


class PermisosFotoTests(FotoPerfilBase):
    def test_sin_token_401(self):
        self.assertEqual(self.subir(imagen('PNG')).status_code, 401)

    def test_cliente_403(self):
        self.autenticar(self.crear_cliente().usuario)

        self.assertEqual(self.subir(imagen('PNG')).status_code, 403)

    def test_admin_403(self):
        self.autenticar(self.crear_admin())

        self.assertEqual(self.subir(imagen('PNG')).status_code, 403)

    def test_un_barbero_no_toca_la_foto_de_otro(self):
        otro = self.crear_barbero()
        self.autenticar(self.barbero.usuario)

        self.subir(imagen('PNG'))

        otro.refresh_from_db()
        self.assertFalse(otro.foto_perfil)
        self.assertEqual(otro.foto_perfil_url, '')

    def test_get_no_permitido(self):
        self.autenticar(self.barbero.usuario)

        self.assertEqual(self.client.get(self.url).status_code, 405)
