# Resultados AUT-API — Catálogo y Turnos

- Fecha: 27/10/2026 · API local con Docker Compose, datos `seed_demo`, rama `develop`
- Requests: 49 · Aserciones: 234 · Fallidas: 0

| # | Request | Método | HTTP | Resultado |
|---|---|---|---|---|
| 1 | Setup: Registro cliente OK | POST | 201 | PASA |
| 2 | Setup: Login cliente OK | POST | 200 | PASA |
| 3 | Setup: Login admin | POST | 200 | PASA |
| 4 | Setup: Login barbero | POST | 200 | PASA |
| 5 | Servicio: crear como admin | POST | 201 | PASA |
| 6 | Servicio: GET detalle (contrato) | GET | 200 | PASA |
| 7 | Servicios: listar (público) | GET | 200 | PASA |
| 8 | Servicio: crear como cliente -> 403 | POST | 403 | PASA |
| 9 | Servicio: crear sin token -> 401 | POST | 401 | PASA |
| 10 | Servicio: duración 0 -> 400 | POST | 400 | PASA |
| 11 | Servicio: precio negativo -> 400 | POST | 400 | PASA |
| 12 | Servicio: editar precio (PATCH) | PATCH | 200 | PASA |
| 13 | Barberos: listar y tomar uno | GET | 200 | PASA |
| 14 | Horario: crear como admin | POST | 201 | PASA |
| 15 | Horario: GET detalle (contrato) | GET | 200 | PASA |
| 16 | Horario: PATCH intervalo | PATCH | 200 | PASA |
| 17 | Horario: hora fin <= inicio -> 400 | POST | 400 | PASA |
| 18 | Horario: crear como cliente -> 403 | POST | 403 | PASA |
| 19 | Oferta barbero-servicio: crear | POST | 201 | PASA |
| 20 | Oferta: GET detalle (contrato) | GET | 200 | PASA |
| 21 | Oferta: PATCH precio personalizado | PATCH | 200 | PASA |
| 22 | Oferta barbero-servicio: duplicada -> 400 | POST | 400 | PASA |
| 23 | Oferta: listar por barbero (público) | GET | 200 | PASA |
| 24 | Reservar turno OK (cliente) | POST | 201 | PASA |
| 25 | Reservar mismo horario -> 400 | POST | 400 | PASA |
| 26 | Reservar en el pasado -> 400 | POST | 400 | PASA |
| 27 | Reservar fuera del horario del barbero -> 400 | POST | 400 | PASA |
| 28 | Reservar sin token -> 401 | POST | 401 | PASA |
| 29 | Reservar como barbero -> 403 | POST | 403 | PASA |
| 30 | Reservar sin campos obligatorios -> 400 | POST | 400 | PASA |
| 31 | Mis turnos (cliente) incluye el reservado | GET | 200 | PASA |
| 32 | Mis turnos sin token -> 401 | GET | 401 | PASA |
| 33 | Agenda (/turnos/) como cliente -> 403 | GET | 403 | PASA |
| 34 | Agenda como admin -> 200 | GET | 200 | PASA |
| 35 | Agenda filtrada por estado | GET | 200 | PASA |
| 36 | Cambiar estado a confirmado (admin) | PATCH | 200 | PASA |
| 37 | Cambiar a estado inválido -> 400 | PATCH | 400 | PASA |
| 38 | Cliente no puede PATCH estado -> 403 | PATCH | 403 | PASA |
| 39 | Servicios más solicitados | GET | 200 | PASA |
| 40 | Cancelar turno inexistente -> 404 | PATCH | 404 | PASA |
| 41 | Cancelar turno propio (cliente) | PATCH | 200 | PASA |
| 42 | Cancelar turno ya cancelado -> 400 | PATCH | 400 | PASA |
| 43 | Oferta: DELETE (baja lógica) | DELETE | 204 | PASA |
| 44 | Oferta: GET tras DELETE -> inactiva | GET | 200 | PASA |
| 45 | Horario: DELETE (baja lógica) | DELETE | 204 | PASA |
| 46 | Horario: GET tras DELETE -> inactivo | GET | 200 | PASA |
| 47 | Servicio: DELETE (baja lógica) | DELETE | 204 | PASA |
| 48 | Servicio: DELETE sin token -> 401 | DELETE | 401 | PASA |
| 49 | Servicio: GET tras DELETE -> inactivo | GET | 200 | PASA |
