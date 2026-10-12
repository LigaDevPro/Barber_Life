from .base_page import BasePage


class DashboardPage(BasePage):
    """Panel de barbero / administrador."""

    def ir_a_catalogo(self):
        from .catalogo_page import CatalogoPage
        self._navegar_por_menu('Catálogo', '/catalogo')
        return CatalogoPage(self._page, self._base_url)
