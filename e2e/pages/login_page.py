import re

from .base_page import BasePage
from .dashboard_page import DashboardPage
from .inicio_page import InicioPage


class LoginPage(BasePage):
    """Pantalla /login."""

    def __init__(self, page, base_url):
        super().__init__(page, base_url)
        self._email = page.get_by_test_id('login-email')
        self._password = page.get_by_test_id('login-password')
        self._enviar = page.get_by_test_id('login-submit')
        self._errores = page.get_by_test_id(re.compile(r'^login-.*error$'))

    def abrir(self) -> 'LoginPage':
        self._page.goto(f'{self._base_url}/login')
        self._email.wait_for()
        return self

    def intentar_login(self, email: str, password: str) -> 'LoginPage':
        """Completa y envía el formulario; se queda en el login."""
        self._email.fill(email)
        self._password.fill(password)
        self._enviar.click()
        return self

    def iniciar_sesion_como_cliente(self, email: str, password: str) -> InicioPage:
        self.intentar_login(email, password)
        self._page.wait_for_url('**/inicio')
        return InicioPage(self._page, self._base_url)

    def iniciar_sesion_como_staff(self, email: str, password: str) -> DashboardPage:
        self.intentar_login(email, password)
        self._page.wait_for_url('**/dashboard')
        return DashboardPage(self._page, self._base_url)

    def mensaje_de_error(self) -> str:
        """Texto del primer error visible (de campo o general)."""
        self._errores.first.wait_for(state='visible')
        return self._errores.first.inner_text().strip()
