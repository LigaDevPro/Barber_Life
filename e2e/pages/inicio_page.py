from .base_page import BasePage


class InicioPage(BasePage):
    """Pantalla /inicio del cliente."""

    def __init__(self, page, base_url):
        super().__init__(page, base_url)
        self._titulo = page.get_by_role('heading', level=1)

    def titulo(self) -> str:
        self._titulo.wait_for()
        return self._titulo.inner_text().strip()

    def ir_a_solicitar_turno(self):
        from .solicitar_turno_page import SolicitarTurnoPage
        self._navegar_por_menu('Solicitar turno', '/solicitar-turno')
        return SolicitarTurnoPage(self._page, self._base_url)
