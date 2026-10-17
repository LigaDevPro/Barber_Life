# Changelog

Todos los cambios significativos de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

Sin cambios pendientes.

## [0.3.0] - 2026-10-17

Cierre del Sprint 4 (octubre 2026): línea base integrada a `main` con las cinco funcionalidades obligatorias de la entrega final y la documentación completa del proyecto.

### Agregado
- Backend: filtros de turnos por rango de fechas, estado y texto (combinables), con paginación y mensajes de error ante filtros inválidos.
- Backend: exportación de turnos filtrados a CSV, neutralizando contenido que pueda ejecutarse como fórmula.
- Backend: correos electrónicos de bienvenida y de cambio de estado de turnos (SMTP), tolerantes a fallos.
- Backend: carga y borrado de foto de perfil del barbero (JPEG, PNG o WebP de hasta 2 MB, validada por contenido).
- Backend: notificaciones en tiempo real por WebSocket (Django Channels + Daphne) autenticadas por usuario.
- Backend: inicio de sesión y registro con Google (validación del ID token en el servidor).
- Backend: CRUD de horarios y oferta de servicios del barbero.
- Backend: pruebas automáticas de las nuevas funcionalidades (la suite del backend llega a 192 pruebas).
- Frontend: filtros y botón "Exportar CSV" en la gestión de turnos.
- Frontend: subida y borrado de foto en el perfil del barbero.
- Frontend: notificaciones en vivo con reconexión automática.
- Frontend: botón de Google en login y registro.
- Frontend: botón "Cancelar" en Mis turnos y pantalla Catálogo con pestañas Horarios y Oferta.
- Variables de entorno `GOOGLE_CLIENT_ID`, `EMAIL_*` y `MEDIA_ROOT`.
- Documentación del Sprint 4: IEEE 830, requisitos RF/RNF, matriz de trazabilidad, diagrama de Gantt, plan de gestión, informe de avances y manual de usuario.

### Cambiado
- El backend se ejecuta sobre Daphne (ASGI) para atender también WebSockets.
- README actualizado con las nuevas funcionalidades, variables de entorno, ejecución de tests y estado del proyecto.

### Limitaciones conocidas
- No hay recuperación de contraseña ni bloqueo por intentos fallidos de inicio de sesión.
- No se pueden reprogramar turnos.
- El alta de barberos y clientes se hace desde el panel de administración de Django.
- El historial de pagos solo está disponible por API (`GET /api/pagos/`).

## [0.2.0] - 2026-09-21

Cierra el ciclo completo de CRUD del proyecto: todo el backend (Paquetes 1 a 6)
y el frontend que lo consume, tanto para el rol Cliente como para la
administración de Barbero/Admin.

### Agregado
- Backend: perfiles de Cliente y Barbero (`/clientes/me/`, `/barberos/`, `/barberos/me/`).
- Backend: reserva y cancelación de turnos por el cliente, y `mis-turnos` para que liste los propios.
- Backend: CRUD de catálogo (Servicio, Horario, BarberoServicio) con soft delete.
- Backend: integración de pagos con Mercado Pago (Checkout Pro).
- Backend: notificaciones (Mongo) con paginación real.
- Backend: CRUD de Reseñas (calificación de turnos completados).
- Frontend: infraestructura común (modelos, servicios por dominio, topbar con navegación por rol).
- Frontend: portal del Cliente — Inicio (landing con servicios y equipo), Solicitar turno (wizard de 4 pasos), Mis turnos (listado y cancelación), Mi perfil.
- Frontend: ícono de notificaciones con contador y listado.
- Frontend: catálogo admin para gestionar Servicio, Horario y BarberoServicio (Barbero gestiona lo propio, Admin cualquier barbero).

### Cambiado
- Migración del frontend a Tailwind CSS v4.
- README actualizado con cuentas de cliente de prueba, estado del proyecto y enlace de Pagos en la tabla de arquitectura tecnológica.

### Corregido
- Race condition, validaciones y bypass de admin en la reserva de turnos.
- Precio de Turno con horario inactivo, y duplicación en Usuario y perfiles propios.
- Paginación de Barberos y consistencia de horarios.
- Timezone en notificaciones (Mongo).
- Nombre de `urls/__init__.py` que rompía el import.
- Dockerfile del frontend (error cíclico) y variables de entorno de docker-compose.

## [0.1.0] - 2026-08-21

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

[Unreleased]: https://github.com/LigaDevPro/Barber_Life/compare/v0.3.0...develop
[0.3.0]: https://github.com/LigaDevPro/Barber_Life/releases/tag/v0.3.0
[0.2.0]: https://github.com/LigaDevPro/Barber_Life/releases/tag/v0.2.0
[0.1.0]: https://github.com/LigaDevPro/Barber_Life/releases/tag/v0.1.0
