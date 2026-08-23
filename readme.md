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

## 📋 Descripción

**Barber Life** es una plataforma web diseñada para digitalizar y optimizar la operación de barberías y peluquerías. Reemplaza los procesos manuales tradicionales — agendas en papel, turnos por WhatsApp, cobros sin registro — con un sistema moderno, escalable y accesible para clientes, barberos y administradores.

---

## 🎯 Funcionalidades principales

- 📅 Reserva de turnos online con disponibilidad en tiempo real
- 👤 Gestión de usuarios con roles diferenciados (cliente, barbero, administrador)
- ✂️ Catálogo de servicios con precios y duraciones
- 🗓️ Administración de agendas por barbero
- 💳 Procesamiento de pagos digitales mediante **Mercado Pago**
- 🔔 Notificaciones automáticas de confirmación y recordatorios
- ⭐ Sistema de reseñas y calificaciones
- 📊 Panel de estadísticas y métricas para administradores

---

## 🏗️ Arquitectura Tecnológica

El proyecto implementa una arquitectura **Cliente-Servidor** separada en dos repositorios:

| Capa | Tecnología | Repositorio |
|---|---|---|
| Frontend | Angular + TypeScript | [/frontend](https://github.com/LigaDevPro/Barber_Life/tree/main/frontend) |
| Backend | Django + Python | [/backend](https://github.com/LigaDevPro/Barber_Life/tree/main/backend) |
| Base de datos | PostgreSQL + MongoDB | [/backend](https://github.com/LigaDevPro/Barber_Life/tree/main/backend) |
| Infraestructura | Docker + Docker Compose | [/Raíz](https://github.com/LigaDevPro/Barber_Life/tree/main/) - [/backend](https://github.com/LigaDevPro/Barber_Life/tree/main/backend) |
| Pagos | Mercado Pago API | — |

---

## 🚀 Instalación y puesta en marcha

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
SECRET_KEY=tu_secret_key
DEBUG=True
DB_NAME=barberlife
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
MERCADOPAGO_ACCESS_TOKEN=tu_token
```

Aplicar migraciones, cargar datos de demo e iniciar el servidor:

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

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

> Si preferís correr el frontend por fuera de Docker (por ejemplo con `pnpm start`), levantá solo el resto de los servicios: `docker compose up --build postgres mongo backend`.

---

## 🔀 Estructura de trabajo

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
| Fabricio Agustín Gibaut | QA & DevOps — integración de la SPA y routing |

---

## 👥 Equipo de Desarrollo — LigaDevPro

| Integrante | Rol |
|---|---|
| Ignacio Cantoni | Scrum Master |
| Agustín Ceballos | Backend |
| Pablo Peralta | Frontend & UX |
| Rodrigo Rojas | Backend |
| Miguel Scaccia | Product Owner |
| Fabricio Agustín Gibaut | QA & DevOps |

---

## 📈 Estado del proyecto

- ✅ Análisis del problema
- ✅ Relevamiento de requerimientos
- ✅ Diseño de arquitectura
- 🔄 Modelado de base de datos
- 🔄 Desarrollo de funcionalidades
- 🔄 Testing e integración
- ⏳ Despliegue final

---

<p align="center">
  © 2026 <strong>LigaDevPro</strong> — Proyecto académico
</p>