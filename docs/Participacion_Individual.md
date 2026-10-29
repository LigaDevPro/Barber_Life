# Barber Life — Participación individual en QA
 
Tabla de autoría por integrante: cada uno tiene al menos un test automatizado o un hallazgo de accesibilidad. La autoría se verificó con el historial de Git de la rama `develop` (`git log --follow -- <archivo>`): se considera autor de un archivo a quien lo creó y a quienes lo ampliaron con commits propios. Los 13 archivos de test del backend suman **192 tests** y la suite E2E, **45 tests**.
 
Última actualización: 29/10/2026 (cierre del Sprint 4).
 
| Integrante | Rol | Test automatizado | Código | Aporte adicional |
|---|---|---|---|---|
| Ignacio Cantoni | Scrum Master | Backend: `test_turnos.py`, `test_metodos_no_permitidos.py` y `test_auth_permisos.py` (ampliación). E2E de accesibilidad: `e2e/tests/test_accesibilidad.py`, `test_accesibilidad_teclado.py` y `e2e/pages/auditoria_axe.py` | AUT-BE, ACC | Plan de Pruebas, planilla, re-tests, informe de accesibilidad con la evidencia del antes y el después (axe, Lighthouse, trace del fallo E2E) y recorrido con NVDA; correcciones de accesibilidad A11Y-11, A11Y-12 y A11Y-13 |
| Miguel Scaccia | Product Owner | Base de los tests de backend (`base.py`, `test_infra.py`) y toda la estructura E2E: Page Objects, `conftest.py`, `pytest.ini` y los flujos `test_autenticacion.py`, `test_catalogo_servicios.py` y `test_reserva_turno.py` | AUT-BE, AUT-E2E | Criterios de aceptación y validación de las HU; accesibilidad de la barra superior |
| Agustín Ceballos | Backend | Backend: `test_catalogo.py`, `test_perfiles.py`, `test_notificaciones_resenas.py`, `test_emails.py`, `test_turnos_filtros_exportacion.py` y `test_websocket_notificaciones.py` | AUT-BE | Correcciones de bugs del Sprint 3 (PR #94 y PR #156, que corrige el bug #90) |
| Rodrigo Rojas | Backend | Backend: `test_pagos.py` y `test_notificaciones_resenas.py`. API: colección Postman `tests/api/auth-rbac/` | AUT-BE, AUT-API | Reportes Newman (HTML, JUnit y JSON) y `resultados.md` de Autenticación y RBAC |
| Pablo Peralta | Frontend y UX | Backend: `test_auth_permisos.py`, `test_catalogo.py`, `test_perfiles.py`, `test_foto_perfil.py` y `test_login_google.py`. API: colección Postman `tests/api/catalogo-turnos/` | AUT-BE, AUT-API | Reportes Newman y `resultados.md` de Catálogo y turnos; corrección de accesibilidad de login y registro (etiquetas, errores y landmarks) |
 
Fabricio Agustín Gibaut participó hasta el Sprint 3 y dejó el equipo; su cuenta de GitHub (`Agustin-Gibaut-cmd`) figura como asignada en algunos Issues antiguos.
 
## Diseñador y ejecutor
 
Para cada capa, quién diseñó (escribió) el test, según el `git blame` de la línea `def test_` de cada uno, y quién lo ejecuta o lo revisa antes de integrarlo a `develop`. Las columnas equivalentes están en la Planilla de pruebas y en la Matriz de trazabilidad.
 
| Capa | Diseñó | Revisó y ejecutó (PR + CI) |
|---|---|---|
| Backend `test_turnos.py`, `test_metodos_no_permitidos.py` | Ignacio | Otro integrante aprobó el PR; el CI corre la suite completa |
| Backend `test_catalogo.py`, `test_emails.py`, `test_turnos_filtros_exportacion.py`, `test_websocket_notificaciones.py` | Agustín | Otro integrante aprobó el PR; el CI corre la suite completa |
| Backend `test_pagos.py`, `test_notificaciones_resenas.py` | Rodrigo | Otro integrante aprobó el PR; el CI corre la suite completa |
| Backend `test_auth_permisos.py`, `test_perfiles.py`, `test_foto_perfil.py`, `test_login_google.py` | Pablo | Otro integrante aprobó el PR; el CI corre la suite completa |
| Backend `base.py`, `test_infra.py` | Miguel | Otro integrante aprobó el PR; el CI corre la suite completa |
| API: colección Autenticación y RBAC | Rodrigo | Se ejecuta con Newman (local y en el CI) |
| API: colección Catálogo y turnos | Pablo | Se ejecuta con Newman (local y en el CI) |
| E2E: flujos críticos | Miguel | Otro integrante aprobó el PR; Playwright corre en el CI |
| E2E: accesibilidad | Ignacio | Otro integrante aprobó el PR; Playwright corre en el CI |
 
**Dónde verificar:** `git log --follow -- <archivo>` sobre cada archivo muestra el autor de los commits, y la pestaña *Files changed* de cada Pull Request muestra quién lo aprobó.
