<p align="center">
  <img src="frontend/public/img/logo.png" alt="Barber Life Logo" width="120"/>
</p>

<h1 align="center">Barber Life</h1>
<p align="center">Sistema integral de gestión y reservas para barberías y peluquerías</p>

<p align="center">
  <img src="https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white"/>
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white"/>
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
</p>

---

## Descripción

**Barber Life** es una plataforma web diseñada para digitalizar y optimizar la operación de barberías y peluquerías. Reemplaza los procesos manuales tradicionales — agendas en papel, turnos por WhatsApp, cobros sin registro — con un sistema moderno, escalable y accesible para clientes, barberos y administradores.

---

## Funcionalidades principales

- Reserva y cancelación de turnos online (cancelación hasta 2 horas antes) con validación de disponibilidad
- Gestión de usuarios con roles diferenciados (cliente, barbero, administrador) y login con correo/contraseña (JWT) o **con Google**
- Catálogo de servicios con precios y duraciones; horarios y oferta de servicios por barbero
- Agenda de turnos por barbero con **filtros** (fechas, estado, texto), paginación y **exportación a CSV**
- Procesamiento de pagos digitales mediante **Mercado Pago**
- Notificaciones **en tiempo real** (WebSocket) y registro de auditoría en MongoDB
- Correos de bienvenida y de estado de turnos
- Foto de perfil del barbero (JPEG/PNG/WebP, hasta 2 MB)
- Sistema de reseñas y calificaciones
- Panel de estadísticas, ingresos y ranking de barberos para administradores

---

## Arquitectura Tecnológica

El proyecto implementa una arquitectura **Cliente-Servidor** separada en dos repositorios:

| Capa | Tecnología | Repositorio |
|---|---|---|
| Frontend | Angular 21 + TypeScript + Tailwind | [/frontend](https://github.com/LigaDevPro/Barber_Life/tree/main/frontend) |
| Backend | Django 6 + Django REST Framework + Channels/Daphne (ASGI) | [/backend](https://github.com/LigaDevPro/Barber_Life/tree/main/backend) |
| Base de datos | PostgreSQL + MongoDB | [/backend](https://github.com/LigaDevPro/Barber_Life/tree/main/backend) |
| Infraestructura | Docker + Docker Compose | [/Raíz](https://github.com/LigaDevPro/Barber_Life/tree/main/) - [/backend](https://github.com/LigaDevPro/Barber_Life/tree/main/backend) |
| Pagos | Mercado Pago API |
| Autenticación | JWT (SimpleJWT) + Google Identity Services | [/backend](https://github.com/LigaDevPro/Barber_Life/tree/main/backend) - [/frontend](https://github.com/LigaDevPro/Barber_Life/tree/main/frontend) |

---

## Instalación y puesta en marcha

### Requisitos previos

- [Node.js](https://nodejs.org/) v22.13 o superior (requerido por pnpm 11 y Angular 21) — se recomienda usar [nvm](https://github.com/nvm-sh/nvm) ([nvm-windows](https://github.com/coreybutler/nvm-windows) en Windows) para manejar la versión
- [pnpm](https://pnpm.io/) v11.2.2
- [Python](https://www.python.org/) v3.14.3
- [Docker](https://www.docker.com/) y Docker Compose
- [Git](https://git-scm.com/)

---

### 1. Clonar el repositorio

```bash
git clone https://github.com/LigaDevPro/Barber_Life.git
cd Barber_Life
```

---

### 2. Configurar el Backend (Django)

```bash
cd backend
```

Crear y activar el entorno virtual:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Configurar variables de entorno — crear un archivo `.env` en `/backend`:

```env
DJANGO_SECRET_KEY=tu_secret_key
DEBUG=True
POSTGRES_DB=barberlife
POSTGRES_USER=barberlife
POSTGRES_PASSWORD=tu_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
MONGO_URI=mongodb://localhost:27017
MERCADOPAGO_ACCESS_TOKEN=tu_token
FRONTEND_URL=http://localhost:4200

# Login con Google (opcional): Client ID de OAuth 2.0 (tipo "Aplicación web")
GOOGLE_CLIENT_ID=tu_client_id.apps.googleusercontent.com

# Correo (opcional): sin EMAIL_HOST los correos se escriben en la consola
EMAIL_HOST=smtp.ejemplo.com
EMAIL_PORT=587
EMAIL_HOST_USER=usuario
EMAIL_HOST_PASSWORD=clave
DEFAULT_FROM_EMAIL=Barber Life <no-reply@barberlife.local>

# Opcionales
MEDIA_ROOT=./media            # donde se guardan las fotos de perfil
CANCELACION_LIMITE_HORAS=2
```

> Los nombres y valores por defecto de todas las variables están en `backend/core/settings.py`.

Aplicar migraciones, cargar datos de demo e iniciar el servidor:

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

> El proyecto usa **Daphne** (ASGI) para atender también las notificaciones en tiempo real por WebSocket (`ws/notificaciones/`); `runserver` ya arranca sobre Daphne.

> El backend requiere PostgreSQL y MongoDB corriendo (ver sección de Docker Compose más abajo si no los tenés instalados localmente).

El backend queda disponible en `http://localhost:8000`

---

### 3. Configurar el Frontend (Angular)

```bash
cd frontend
```

Activar la versión de Node correcta (si usás nvm):

```bash
nvm install 22.21.0
nvm use 22.21.0
```

Instalar dependencias:

```bash
pnpm install
```

> Si es la primera vez que instalás, pnpm puede pedir aprobar los build scripts de dependencias nativas (`@parcel/watcher`, `esbuild`, `lmdb`, `msgpackr-extract`). El repo ya incluye `pnpm-workspace.yaml` con esa aprobación, así que no debería hacer falta correr `pnpm approve-builds` manualmente.

Iniciar el servidor de desarrollo:

```bash
pnpm start
```

El frontend queda disponible en `http://localhost:4200`

---

### 4. Levantar con Docker Compose (recomendado)

Desde la raíz del proyecto:

```bash
docker compose up --build
```

Esto levanta el frontend, backend y bases de datos (PostgreSQL + MongoDB) de forma conjunta. El backend aplica migraciones automáticamente al arrancar.

Cargar datos de demostración (en otra terminal, con los contenedores ya corriendo):

```bash
docker compose exec backend python manage.py seed_demo
```

**Usuarios de prueba:**

| Rol | Usuario | Contraseña |
|---|---|---|
| Admin | `admin@barberlife.com` | `admin1234` |
| Barbero | `barbero@barberlife.com` | `barbero1234` |

> `seed_demo` también crea varios clientes de prueba con contraseña
> `cliente1234` y emails con el patrón `nombre.apellido<N>@mail.com` (por
> ejemplo `carlos.ruiz3@mail.com`) — revisá el comando o la base para ver
> los generados. Algunos incluyen tildes en el email; si tu navegador/teclado
> tiene problemas para escribirlas, usá uno de los que no las lleve.

**Ejecutar los tests del backend** (192 pruebas):

```bash
docker compose exec backend python manage.py test
```

> Las fotos de perfil se guardan en `MEDIA_ROOT`; en Docker conviene montarlo como volumen para que no se pierdan al recrear el contenedor.

> Si preferís correr el frontend por fuera de Docker (por ejemplo con `pnpm start`), levantá solo el resto de los servicios: `docker compose up --build postgres mongo backend`.

---

## Estructura de trabajo

### Estrategia de ramas

El equipo trabaja con **una rama por integrante**, creada a partir de `develop`:

```
main ← develop ← rama-de-cada-integrante (ej: ignacio-cantoni, pablo-peralta, agustin-ceballos...)
```

- Cada integrante desarrolla en su propia rama personal.
- Al finalizar una tarea, se abre un **Pull Request hacia `develop`**.
- `develop` concentra el trabajo integrado de todo el equipo; se prueba ahí antes de promoverlo.
- `main` recibe únicamente el código estable, mediante merge desde `develop`, y representa las líneas base del proyecto (ver [`docs/PGC.md`](docs/PGC.md)).

Esta estrategia se adapta bien a un equipo chico (6 integrantes) donde cada persona suele trabajar en un área relativamente delimitada (backend, frontend, DevOps), evitando la complejidad de un Git Flow completo con ramas de release/hotfix separadas, que aportaría poco valor en esta escala.

### Convenciones del equipo

- **Mensajes de commit**: en español, en modo imperativo, describiendo la acción (`Agrega endpoints de la API: auth, dashboard y turnos`, `Actualiza readme`).
- **Nomenclatura de ramas**: nombre y apellido del integrante en minúsculas y separados por guion (`ignacio-cantoni`, `agustin-gibaut`).
- **Integración**: todo cambio hacia `develop` se hace vía Pull Request en GitHub, no mediante push directo.

### Roles respecto al repositorio

| Integrante | Rol en el repo |
|---|---|
| Ignacio Cantoni | Scrum Master — coordina merges hacia `develop`, resuelve conflictos de integración |
| Agustín Ceballos | Backend — Docker y entorno de desarrollo |
| Pablo Peralta | Frontend & UX — pantallas y componentes visuales |
| Rodrigo Rojas | Backend — servicios de autenticación |
| Miguel Scaccia | Product Owner — estructura inicial del backend y modelos |

---

## Documentación

La documentación del proyecto (plan de gestión, IEEE 830, requisitos RF/RNF, matriz de trazabilidad, diagrama de Gantt, informe de avances y manual de usuario) se entrega por fuera del repositorio. Las líneas base y la gestión de configuración están descriptas en [`docs/PGC.md`](docs/PGC.md).

---

## Equipo de Desarrollo — LigaDevPro

| Integrante | Rol |
|---|---|
| Ignacio Cantoni | Scrum Master |
| Agustín Ceballos | Backend |
| Pablo Peralta | Frontend & UX |
| Rodrigo Rojas | Backend |
| Miguel Scaccia | Product Owner |

---

## Estado del proyecto

- Análisis del problema
- Relevamiento de requerimientos
- Diseño de arquitectura
- Modelado de base de datos
- Desarrollo de funcionalidades (Sprints 0 a 4)
- Testing e integración (192 pruebas automáticas en el backend)
- Cierre de documentación y despliegue final

**Limitaciones conocidas:** no hay recuperación de contraseña ni bloqueo por intentos fallidos, no se pueden reprogramar turnos, el alta de barberos/clientes se hace desde el panel de administración de Django y el historial de pagos solo está disponible por API (`GET /api/pagos/`).

---

<p align="center">
  © 2026 <strong>LigaDevPro</strong> — Proyecto académico
</p>
