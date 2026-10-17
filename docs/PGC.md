# Plan de Gestión de la Configuración (PGC)

**Proyecto:** Barber Life
**Equipo:** LigaDevPro
**Materia:** Ingeniería de Software — ISPC
**Fecha:** Octubre 2026

> Este documento describe cómo el equipo gestiona la configuración del proyecto
> **Barber Life** en su conjunto. Se presenta como evidencia para la materia
> Ingeniería de Software, pero las prácticas descriptas (versionado, componentes,
> líneas base) se aplican al proyecto completo, no son exclusivas de esta entrega.

## 1. Versionado del producto

El equipo utiliza **versionado semántico (SemVer)**, con el formato `MAYOR.MENOR.PARCHE`:

- **MAYOR**: cambios incompatibles o rediseños grandes de la arquitectura (por ejemplo, cambio de framework o de modelo de datos que rompa compatibilidad).
- **MENOR**: nuevas funcionalidades que no rompen lo existente (por ejemplo, agregar el módulo de turnos o el de autenticación).
- **PARCHE**: correcciones de bugs y ajustes menores que no agregan funcionalidad nueva.

Mientras el proyecto está en desarrollo activo y sin release formal, se usa `0.x.y`, reservando `1.0.0` para la primera versión considerada estable y utilizable de punta a punta (registro, login, gestión de turnos y dashboard funcionando en conjunto).

El detalle de cada versión se documenta en [`CHANGELOG.md`](../CHANGELOG.md), en la raíz del repositorio. Los cambios que están en `develop` pero todavía no forman parte de una línea base figuran en la sección `[Unreleased]`.

**Historial de versiones:**

| Versión | Fecha | Alcance |
|---|---|---|
| `v0.1.0` | 2026-08-21 | Cierre del Sprint 2: estructura inicial, autenticación, dashboard y turnos. |
| `v0.2.0` | 2026-09-21 | CRUD completo de backend y portal del Cliente: catálogo, pagos con Mercado Pago, reseñas y notificaciones. |
| `v0.3.0` | 2026-10-17 | Cierre del Sprint 4: filtros y exportación a CSV, correos, foto de perfil, notificaciones en tiempo real, inicio de sesión con Google, cancelación de turnos y catálogo de horarios/oferta. |

## 2. Componentes del producto

El producto se organiza en dos grandes componentes, cada uno con su propio ciclo de build y despliegue:

| Componente | Descripción | Ubicación en el repo |
|---|---|---|
| **Backend** | API REST en Django + Django REST Framework, ejecutada sobre Daphne (ASGI) para atender también WebSockets (Django Channels). Maneja autenticación (JWT y Google), lógica de negocio, correos, archivos subidos (fotos de perfil) y persistencia en PostgreSQL (datos relacionales: usuarios, turnos, pagos) y MongoDB (notificaciones y log de auditoría). | `/backend` |
| **Frontend** | Aplicación Angular (SPA) que consume la API. Incluye las pantallas de login y registro (con Google), dashboard por rol, gestión de turnos con filtros y exportación a CSV, portal del cliente, catálogo, perfil y notificaciones en tiempo real. | `/frontend` |

Ambos componentes se orquestan juntos mediante `docker-compose.yml` en la raíz del repositorio, junto con los servicios de infraestructura (PostgreSQL y MongoDB). La documentación de cómo levantar el entorno completo está en el [`README.md`](../README.md) del repositorio.

Artefactos de configuración relevantes por componente:
- Backend: `backend/requirements.txt` (dependencias Python), `backend/.env` (variables de entorno, no versionado; incluye `GOOGLE_CLIENT_ID`, `EMAIL_*` y `MEDIA_ROOT`), `backend/Dockerfile`.
- Frontend: `frontend/package.json` y `frontend/pnpm-lock.yaml` (dependencias Node), `frontend/pnpm-workspace.yaml` (permisos de build scripts), `frontend/Dockerfile`.

## 3. Criterio de línea base (baseline)

El equipo considera que una versión queda **congelada como línea base** cuando:

1. El código fue integrado a la rama `develop` mediante un Pull Request revisado (no directamente a `develop` sin PR).
2. El proyecto compila y levanta correctamente con `docker compose up --build` sin errores.
3. Las pruebas automáticas del backend pasan (`python manage.py test`; 192 pruebas al cierre del Sprint 4).
4. Las funcionalidades incluidas en esa línea base fueron probadas manualmente por al menos un integrante distinto de quien la desarrolló.

Los merges de `develop` hacia `main` representan las líneas base "oficiales" del proyecto — puntos de referencia estables que corresponden al cierre de un sprint o a un hito del proyecto ABP. Cada línea base en `main` se marca con un **tag de Git** siguiendo el versionado semántico (por ejemplo `v0.1.0`) y queda reflejada como una entrada en el `CHANGELOG.md`.

**Ejemplos aplicados:**

- La línea base `v0.1.0` corresponde al cierre del Sprint 2 del proyecto (estructura inicial de frontend y backend, endpoints de autenticación/dashboard/turnos, y la configuración de Docker). Esta misma línea base es la que el equipo toma como evidencia para la entrega de la Evidencia Valorativa 4 de Ingeniería de Software.
- La línea base `v0.2.0` cierra el ciclo completo de CRUD del proyecto, tanto en backend como en el frontend que lo consume.
- La línea base `v0.3.0` corresponde al cierre del Sprint 4: los cambios se integraron en `develop` mediante los Pull Requests #158 a #166, se promovieron a `main` y se marcaron con el tag `v0.3.0`. Es la versión de la entrega final del proyecto.

## 4. Control de cambios
