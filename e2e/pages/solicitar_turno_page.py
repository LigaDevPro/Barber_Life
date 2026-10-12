from .base_page import BasePage


class SolicitarTurnoPage(BasePage):
    """Pantalla /solicitar-turno: servicio → barbero → fecha/hora → pago."""

    def __init__(self, page, base_url):
        super().__init__(page, base_url)
        self._servicios = page.get_by_test_id('turno-servicio')
        self._barberos = page.get_by_test_id('turno-barbero')
        self._dias = page.get_by_test_id('turno-dia')
        self._horas = page.get_by_test_id('turno-hora')
        self._pago_en_local = page.get_by_test_id('turno-pago-efectivo')
        self._confirmar = page.get_by_test_id('turno-confirmar')
        self._exito = page.get_by_test_id('turno-exito')

    def elegir_servicio(self, nombre: str) -> 'SolicitarTurnoPage':
        self._servicios.filter(has_text=nombre).first.click()
        return self

    def elegir_primer_barbero(self) -> 'SolicitarTurnoPage':
        self._barberos.first.click()
        return self

    def elegir_ultimo_dia_y_primer_horario(self) -> 'SolicitarTurnoPage':
        """Elige un día futuro (el último ofrecido) y su primer horario."""
        self._dias.last.click()
        self._horas.first.click()
        return self

    def horarios_ofrecidos_hoy(self, dia_de_hoy: int) -> list[str]:
        """Horarios que la pantalla ofrece para hoy; vacío si hoy no es un día elegible."""
        primer_dia = self._dias.first
        primer_dia.wait_for()
        if primer_dia.inner_text().split()[-1] != str(dia_de_hoy):
            return []
        primer_dia.click()
        self._horas.first.wait_for()
        return [h.inner_text().strip() for h in self._horas.all()]

    def pagar_en_el_local(self) -> 'SolicitarTurnoPage':
        self._pago_en_local.click()
        return self

    def confirmar(self) -> 'SolicitarTurnoPage':
        self._confirmar.click()
        self._exito.wait_for()
        return self

    def titulo_de_confirmacion(self) -> str:
        return self._exito.inner_text().strip()
