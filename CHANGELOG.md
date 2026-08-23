# Changelog

Todos los cambios significativos de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

# Released

Cambios integrados a `main` que forman parte de una línea base.

# 0.1.0 - 2026-08-21

Cierre del Sprint 2 del proyecto. Esta línea base es además la que se toma como
evidencia para la Evidencia Valorativa 4 de Ingeniería de Software (Gestión de
la Configuración y Desarrollo Colaborativo), pero corresponde al estado real
y completo del código del proyecto a esta fecha, no a un recorte hecho para
la materia.

### Agregado
- Estructura inicial del proyecto Angular (frontend) y configuración base.
- Estructura inicial del backend: modelos y configuración de Django.
- Endpoints de la API: autenticación (registro, login, refresh, me), dashboard y turnos.
- Servicios de autenticación, guards e interceptor de JWT en el frontend.
- Integración del esqueleto de la SPA en Angular con routing.
- Pantallas de login, dashboard y turnos en el frontend.
- Configuración de Docker y Docker Compose para frontend, backend, PostgreSQL y MongoDB.
- Logo del proyecto.
- `.gitignore` y plantilla de variables de entorno.
- Plan de Gestión de la Configuración (`docs/PGC.md`).
- Este `CHANGELOG.md`.

### Cambiado
- Actualización del README con instrucciones de instalación, estructura de trabajo del equipo y roles.
- Ajuste de variables de entorno de Docker Compose para la conexión entre servicios.

[Released]: https://github.com/LigaDevPro/Barber_Life/compare/v0.1.0...develop
[0.1.0]: https://github.com/LigaDevPro/Barber_Life/releases/tag/v0.1.0
