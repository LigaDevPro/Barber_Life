from .base_page import BasePage
from playwright.sync_api import Error as PlaywrightError


class InicioPage(BasePage):
    """Pantalla /inicio del cliente."""

    def __init__(self, page, base_url):
        super().__init__(page, base_url)
        self._titulo = page.get_by_role('heading', level=1)
        self._barberos = page.get_by_test_id('inicio-barbero')
        self._dialogo = page.get_by_role('dialog')

    def titulo(self) -> str:
        self._titulo.wait_for()
        return self._titulo.inner_text().strip()

    def ir_a_solicitar_turno(self):
        from .solicitar_turno_page import SolicitarTurnoPage
        self._navegar_por_menu('Solicitar turno', '/solicitar-turno')
        return SolicitarTurnoPage(self._page, self._base_url)

    def abrir_perfil_del_primer_barbero(self) -> None:
        """Abre con el mouse el diálogo con el perfil del primer barbero."""
        self._barberos.first.click()
        self._dialogo.wait_for()

    def recorrer_con_tab(self, veces: int) -> None:
        for _ in range(veces):
            self._page.keyboard.press('Tab')

    def cerrar_con_escape(self) -> None:
        self._page.keyboard.press('Escape')

    def dialogo_esta_abierto(self) -> bool:
        """True si el diálogo sigue visible tras esperar hasta 3 s a que se cierre."""
        try:
            self._dialogo.wait_for(state='hidden', timeout=3000)
            return False
        except PlaywrightError:
            return True

    def foco_esta_dentro_del_dialogo(self) -> bool:
        return self._page.evaluate("!!document.activeElement?.closest('[role=dialog]')")
