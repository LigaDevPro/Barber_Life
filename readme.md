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

- [Node.js](https://nodejs.org/) v24.14.1
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

Aplicar migraciones e iniciar el servidor:

```bash
python manage.py migrate
python manage.py runserver
```

El backend queda disponible en `http://localhost:8000`

---

### 3. Configurar el Frontend (Angular)

```bash
cd frontend
```

Instalar dependencias:

```bash
pnpm install
```

Iniciar el servidor de desarrollo:

```bash
ng serve
```

El frontend queda disponible en `http://localhost:4200`

---

### 4. Levantar con Docker Compose (recomendado)

Desde la raíz del proyecto:

```bash
docker-compose up --build
```

Esto levanta el frontend, backend y base de datos de forma conjunta.

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
