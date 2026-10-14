import json
import urllib.request

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page

ETIQUETAS_WCAG = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']
IMPACTOS_BLOQUEANTES = ('critical', 'serious')


class AuditoriaAxe:
    """Auditoría de accesibilidad (axe-core) de una pantalla de la SPA.

    No contiene aserciones: devuelve los datos para que el test decida.
    """

    def __init__(self, page: Page, base_url: str, api_url: str):
        self._page = page
        self._base_url = base_url
        self._api_url = api_url

    def iniciar_sesion_por_api(self, email: str, password: str) -> None:
        """Deja la sesión abierta en el navegador sin pasar por la UI de login."""
        req = urllib.request.Request(
            f'{self._api_url}/auth/login/',
            data=json.dumps({'email': email, 'password': password}).encode(),
            headers={'Content-Type': 'application/json'}, method='POST',
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            sesion = json.load(resp)
        self._page.add_init_script(
            "localStorage.setItem('bl_access_token', %s);"
            "localStorage.setItem('bl_refresh_token', %s);"
            "localStorage.setItem('bl_usuario', %s);"
            % (json.dumps(sesion['access']), json.dumps(sesion['refresh']), json.dumps(json.dumps(sesion['usuario'])))
        )

    def abrir(self, ruta: str) -> 'AuditoriaAxe':
        self._page.goto(f'{self._base_url}{ruta}')
        self._page.wait_for_load_state('networkidle')
        return self

    def violaciones_bloqueantes(self) -> list[dict]:
        """Violaciones WCAG 2.2 AA de impacto critical o serious."""
        resultado = Axe().run(self._page, options={'runOnly': {'type': 'tag', 'values': ETIQUETAS_WCAG}})
        return [v for v in resultado.response['violations'] if v['impact'] in IMPACTOS_BLOQUEANTES]

    def titulo(self) -> str:
        return self._page.title()

    def idioma(self) -> str:
        return self._page.evaluate('document.documentElement.lang')

    def tiene_scroll_horizontal(self) -> bool:
        return self._page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth + 1')

    def ajustar_ancho(self, ancho: int, alto: int = 800) -> None:
        self._page.set_viewport_size({'width': ancho, 'height': alto})
