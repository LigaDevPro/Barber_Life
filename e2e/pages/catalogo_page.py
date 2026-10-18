from .base_page import BasePage


class CatalogoPage(BasePage):
    """Pantalla /catalogo, pestaña Servicios (vista de administrador)."""

    def __init__(self, page, base_url):
        super().__init__(page, base_url)
        self._nombre = page.get_by_test_id('servicio-nombre')
        self._duracion = page.get_by_test_id('servicio-duracion')
        self._precio = page.get_by_test_id('servicio-precio')
        self._guardar = page.get_by_test_id('servicio-guardar')
        self._items = page.get_by_test_id('servicio-item')

    def _item(self, nombre: str):
        return self._items.filter(has_text=nombre)

    def crear_servicio(self, nombre: str, duracion: int, precio: str) -> 'CatalogoPage':
        self._nombre.fill(nombre)
        self._duracion.fill(str(duracion))
        self._precio.fill(precio)
        self._guardar.click()
        self._item(nombre).wait_for()
        return self

    def editar_precio(self, nombre: str, nuevo_precio: str) -> 'CatalogoPage':
        self._item(nombre).get_by_test_id('servicio-editar').click()
        self._precio.fill(nuevo_precio)
        self._guardar.click()
        self._item(nombre).filter(has_text=f'${nuevo_precio}').wait_for()
        return self

    def desactivar_servicio(self, nombre: str) -> 'CatalogoPage':
        self._item(nombre).get_by_test_id('servicio-toggle').click()
        self._item(nombre).filter(has_text='inactivo').wait_for()
        return self

    def detalle_de(self, nombre: str) -> str:
        """Texto completo de la fila del servicio (nombre, duración, precio, estado)."""
        item = self._item(nombre)
        item.wait_for()
        return ' '.join(item.inner_text().split())

    def cantidad_de(self, nombre: str) -> int:
        return self._item(nombre).count()
