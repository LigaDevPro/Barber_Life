# Barber Life — Participación individual en QA

Tabla de autoría por integrante: cada uno tiene al menos un test automatizado o un hallazgo de accesibilidad. La autoría se verificó con el historial de Git de la rama `develop` (archivos de test que cada integrante agregó o modificó).

Última actualización: 15/10/2026 (Sprint 4).

| Integrante | Rol | Test automatizado | Código | Aporte adicional |
|---|---|---|---|---|
| Ignacio Cantoni | Scrum Master | `backend/gestion/tests/test_auth_permisos.py`, `test_turnos.py`, `test_perfiles.py`, `test_notificaciones_resenas.py`, `test_metodos_no_permitidos.py`; E2E `e2e/tests/test_accesibilidad.py` y `test_accesibilidad_teclado.py` | AUT-BE, ACC | Plan de Pruebas, planilla, re-tests, corrección del bug #90 y evidencia del fallo E2E de accesibilidad |
| Miguel Scaccia | Product Owner | Base de los tests de backend (`tests/base.py`, `test_infra.py`) y estructura E2E (Page Objects, `conftest.py`, `pytest.ini`) | AUT-BE, AUT-E2E | Criterios de aceptación y validación de las HU |
| Agustín Ceballos | Backend | `backend/gestion/tests/test_catalogo.py`, `test_perfiles.py`, `test_notificaciones_resenas.py` | AUT-BE | Correcciones de bugs del Sprint 3 (PR #94 y #156) |
| Rodrigo Rojas | Backend | `backend/gestion/tests/test_pagos.py`, `test_auth_permisos.py`, `test_notificaciones_resenas.py`; colección Postman `tests/api/auth-rbac/` | AUT-BE, AUT-API | Reportes Newman (HTML, JUnit y JSON) y `resultados.md` de Auth y RBAC |
| Pablo Peralta | Frontend y UX | `backend/gestion/tests/test_catalogo.py`, `test_auth_permisos.py`, `test_perfiles.py`; colección Postman `tests/api/catalogo-turnos/` | AUT-BE, AUT-API | Reportes Newman y `resultados.md` de Catálogo y turnos; commits de accesibilidad |

Fabricio Agustín Gibaut participó hasta el Sprint 3 y dejó el equipo.

**Dónde verificar:** `git log --follow -- <archivo>` sobre cada archivo muestra el autor de los commits.
