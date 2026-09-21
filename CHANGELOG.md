# Changelog

Todos los cambios significativos de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

# Released

Cambios integrados a `main` que forman parte de una línea base.

# 0.2.0 - 2026-09-21

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

[Released]: https://github.com/LigaDevPro/Barber_Life/compare/v0.2.0...develop
[0.2.0]: https://github.com/LigaDevPro/Barber_Life/releases/tag/v0.2.0
[0.1.0]: https://github.com/LigaDevPro/Barber_Life/releases/tag/v0.1.0
