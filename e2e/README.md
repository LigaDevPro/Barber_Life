# Tests E2E (Playwright + POM)

Flujos críticos de la SPA Angular contra la app real (AUT-E2E).

| Test | Flujo | TC |
|---|---|---|
| `tests/test_autenticacion.py` | Login exitoso + 4 logins inválidos parametrizados | TC-LOGIN-01/02 |
| `tests/test_catalogo_servicios.py` | CRUD de servicios (alta, edición, baja lógica) | TC-CATALOGO-01 |
| `tests/test_reserva_turno.py` | Reserva de turno + no ofrecer horarios que ya pasaron | TC-TURNO-01/02 |
| `tests/test_accesibilidad.py` | axe-core WCAG 2.2 AA, título/idioma y reflow a 320 px en 11 pantallas (parametrizado) | ACC-01/02/03 |
| `tests/test_accesibilidad_teclado.py` | Foco, Esc y `aria-pressed` con teclado | ACC-04/05, A11Y-12/13 |

Son 45 tests: 8 de flujos críticos (incl. 4 logins inválidos), 33 de accesibilidad por pantalla y 4 de teclado.

## Requisitos

- App levantada: `docker compose up` (frontend en `:4200`, API en `:8000`).
- Datos demo cargados (una vez): `docker compose exec backend python manage.py seed_demo`.
- Python 3.10+.

## Ejecutar

```bash
cd e2e
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
.venv/bin/pytest            # headless
.venv/bin/pytest --headed   # viendo el navegador
```

Variables opcionales: `BASE_URL`, `API_URL`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`.

## Reportes

Cada corrida genera un **reporte HTML autocontenido** en `e2e/reportes/reporte_e2e.html` (lo configura `pytest.ini` con `pytest-html`): resultado de cada test, duración y detalle del fallo. Abrilo con el navegador.

- Capturas, videos y traces de los fallos quedan en `e2e/reportes/artefactos/` (no se versionan).
- `e2e/reportes/reporte_e2e.html` sí se puede versionar como evidencia de una corrida.
- En el CI, el job **API (Newman) y E2E (Playwright)** sube el reporte como artefacto `reporte-playwright` en cada ejecución del workflow.

> El test `TC-TURNO-02` fija el reloj del navegador con la zona horaria de la máquina que corre pytest: pytest y el navegador tienen que estar en la misma zona (lo normal, también en el CI).

## Convenciones

- Selectores: `data-testid` → rol ARIA → texto. Sin CSS por clases ni XPath.
- Un Page Object por pantalla (`pages/`), sin aserciones; las aserciones van en los tests.
- Cada test cliente se crea por API (`cliente_nuevo`), no depende de datos previos.
