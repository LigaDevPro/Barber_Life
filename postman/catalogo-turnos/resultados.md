# Resultados AUT-API — Catálogo y Turnos

- Fecha: 13/10/2026 · Entorno: API local (Django 6.1 + PostgreSQL 16 + MongoDB 7), datos `seed_demo`, rama `develop` (PR #115)
- Requests: 39 · Aserciones: 59 · Fallidas: 0

| # | Request | Método | HTTP | Resultado |
|---|---|---|---|---|
| 1 | Setup: Registro cliente OK | POST | 201 | PASA |
| 2 | Setup: Login cliente OK | POST | 200 | PASA |
| 3 | Setup: Login admin | POST | 200 | PASA |
| 4 | Setup: Login barbero | POST | 200 | PASA |
| 5 | Servicios: listar (público) | GET | 200 | PASA |
| 6 | Servicio: crear como admin | POST | 201 | PASA |
| 7 | Servicio: crear como cliente -> 403 | POST | 403 | PASA |
| 8 | Servicio: crear sin token -> 401 | POST | 401 | PASA |
| 9 | Servicio: duración 0 -> 400 | POST | 400 | PASA |
| 10 | Servicio: precio negativo -> 400 | POST | 400 | PASA |
| 11 | Servicio: editar precio (PATCH) | PATCH | 200 | PASA |
| 12 | Barberos: listar y tomar uno | GET | 200 | PASA |
| 13 | Horario: crear como admin | POST | 201 | PASA |
| 14 | Horario: hora fin <= inicio -> 400 | POST | 400 | PASA |
| 15 | Horario: crear como cliente -> 403 | POST | 403 | PASA |
| 16 | Oferta barbero-servicio: crear | POST | 201 | PASA |
| 17 | Oferta barbero-servicio: duplicada -> 400 | POST | 400 | PASA |
| 18 | Oferta: listar por barbero (público) | GET | 200 | PASA |
| 19 | Reservar turno OK (cliente) | POST | 201 | PASA |
| 20 | Reservar mismo horario -> 400 | POST | 400 | PASA |
| 21 | Reservar en el pasado -> 400 | POST | 400 | PASA |
| 22 | Reservar fuera del horario del barbero -> 400 | POST | 400 | PASA |
| 23 | Reservar sin token -> 401 | POST | 401 | PASA |
| 24 | Reservar como barbero -> 403 | POST | 403 | PASA |
| 25 | Reservar sin campos obligatorios -> 400 | POST | 400 | PASA |
| 26 | Mis turnos (cliente) incluye el reservado | GET | 200 | PASA |
| 27 | Mis turnos sin token -> 401 | GET | 401 | PASA |
| 28 | Agenda (/turnos/) como cliente -> 403 | GET | 403 | PASA |
| 29 | Agenda como admin -> 200 | GET | 200 | PASA |
| 30 | Agenda filtrada por estado | GET | 200 | PASA |
| 31 | Cambiar estado a confirmado (admin) | PATCH | 200 | PASA |
| 32 | Cambiar a estado inválido -> 400 | PATCH | 400 | PASA |
| 33 | Cliente no puede PATCH estado -> 403 | PATCH | 403 | PASA |
| 34 | Servicios más solicitados | GET | 200 | PASA |
| 35 | Cancelar turno inexistente -> 404 | PATCH | 404 | PASA |
| 36 | Cancelar turno propio (cliente) | PATCH | 200 | PASA |
| 37 | Cancelar turno ya cancelado -> 400 | PATCH | 400 | PASA |
| 38 | Limpieza: baja lógica del servicio QA | DELETE | 204 | PASA |
| 39 | Limpieza: baja lógica del horario QA | DELETE | 204 | PASA |
