from .base_page import BasePage


class SolicitarTurnoPage(BasePage):
    """Pantalla /solicitar-turno: servicio → barbero → fecha/hora → pago."""

    def __init__(self, page, base_url):
        super().__init__(page, base_url)
        self._servicios = page.get_by_test_id('turno-servicio')
        self._barberos = page.get_by_test_id('turno-barbero')
        self._dias = page.get_by_test_id('turno-dia')
        self._horas = page.get_by_test_id('turno-hora')
        self._sin_horarios = page.get_by_text('No hay horarios para ese día.')
        self._pago_en_local = page.get_by_test_id('turno-pago-efectivo')
        self._confirmar = page.get_by_test_id('turno-confirmar')
        self._exito = page.get_by_test_id('turno-exito')

    def elegir_servicio(self, nombre: str) -> 'SolicitarTurnoPage':
        self._servicios.filter(has_text=nombre).first.click()
        return self

    def elegir_primer_barbero(self) -> 'SolicitarTurnoPage':
        self._barberos.first.click()
        return self

    def reservar_primer_horario_disponible(self) -> 'SolicitarTurnoPage':
        """Confirma el primer horario futuro que el backend acepte.

        La pantalla no sabe qué horarios ya están tomados por otras reservas,
        así que se prueba de a uno (del día más lejano al más cercano) hasta
        que el backend responde 201. Así la acción es repetible entre corridas.
        """
        for i in reversed(range(self._dias.count())):
            self._dias.nth(i).click()
            for j in range(self._horas.count()):
                self._horas.nth(j).click()
                with self._page.expect_response(
                    lambda r: r.request.method == 'POST' and r.url.rstrip('/').endswith('/turnos'),
                ) as respuesta:
                    self._confirmar.click()
                if respuesta.value.ok:
                    self._exito.wait_for()
                    return self
        raise RuntimeError('No hay ningún horario libre para reservar en los días ofrecidos')

    def horarios_ofrecidos_hoy(self, dia_de_hoy: int) -> list[str] | None:
        """Horarios que la pantalla ofrece para hoy (puede ser vacío si ya no
        quedan); None si hoy no es un día elegible."""
        primer_dia = self._dias.first
        primer_dia.wait_for()
        if primer_dia.inner_text().split()[-1] != str(dia_de_hoy):
            return None
        primer_dia.click()
        self._horas.first.or_(self._sin_horarios).wait_for()
        return [h.inner_text().strip() for h in self._horas.all()]

    def pagar_en_el_local(self) -> 'SolicitarTurnoPage':
        self._pago_en_local.click()
        return self

    def titulo_de_confirmacion(self) -> str:
        return self._exito.inner_text().strip()

    def servicios_marcados_como_elegidos(self) -> int:
        """Cantidad de servicios que le avisan al lector de pantalla que están elegidos."""
        return self._servicios.evaluate_all(
            "els => els.filter(e => e.getAttribute('aria-pressed') === 'true').length"
        )

    def pago_en_local_esta_marcado(self) -> bool:
        return self._pago_en_local.get_attribute('aria-pressed') == 'true'
