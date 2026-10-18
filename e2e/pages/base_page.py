from playwright.sync_api import Error as PlaywrightError, Page


class BasePage:
    """Comportamiento común de los Page Objects. No contiene aserciones."""

    def __init__(self, page: Page, base_url: str):
        self._page = page
        self._base_url = base_url

    def _navegar_por_menu(self, opcion: str, ruta: str) -> None:
        """Abre el menú de la barra superior y entra a una opción."""
        self._page.get_by_role('button', name='Menú').click()
        self._page.get_by_role('link', name=opcion, exact=True).click()
        self._page.wait_for_url(f'**{ruta}')

    def foco_esta_en_el_titulo(self) -> bool:
        """True si el foco llega al <h1> de la vista (espera hasta 3 s)."""
        try:
            self._page.wait_for_function("document.activeElement?.tagName === 'H1'", timeout=3000)
            return True
        except PlaywrightError:
            return False
