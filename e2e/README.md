# Tests E2E (Playwright + POM)

Flujos críticos de la SPA Angular contra la app real (AUT-E2E).

| Test | Flujo | TC |
|---|---|---|
| `tests/test_autenticacion.py` | Login exitoso + 4 logins inválidos parametrizados | TC-LOGIN-01/02 |
| `tests/test_catalogo_servicios.py` | CRUD de servicios (alta, edición, baja lógica) | TC-CATALOGO-01 |
| `tests/test_reserva_turno.py` | Reserva de turno + bug conocido (horarios pasados) | TC-TURNO-01/02 |

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
Capturas, videos y traces de los fallos quedan en `e2e/reportes/artefactos/`.

## Convenciones

- Selectores: `data-testid` → rol ARIA → texto. Sin CSS por clases ni XPath.
- Un Page Object por pantalla (`pages/`), sin aserciones; las aserciones van en los tests.
- Cada test cliente se crea por API (`cliente_nuevo`), no depende de datos previos.
