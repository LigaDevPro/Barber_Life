# Resultados AUT-API — Autenticación y RBAC

- Fecha: 27/10/2026 · API local con Docker Compose, datos `seed_demo`, rama `develop`
- Requests: 26 · Aserciones: 115 · Fallidas: 0

| # | Request | Método | HTTP | Resultado |
|---|---|---|---|---|
| 1 | Registro cliente OK | POST | 201 | PASA |
| 2 | Registro email duplicado -> 400 | POST | 400 | PASA |
| 3 | Registro contraseñas distintas -> 400 | POST | 400 | PASA |
| 4 | Registro contraseña débil -> 400 | POST | 400 | PASA |
| 5 | Registro email inválido -> 400 | POST | 400 | PASA |
| 6 | Login cliente OK | POST | 200 | PASA |
| 7 | Login contraseña incorrecta -> 400 | POST | 400 | PASA |
| 8 | Login email inexistente -> 400 | POST | 400 | PASA |
| 9 | Login sin campos -> 400 | POST | 400 | PASA |
| 10 | Login admin | POST | 200 | PASA |
| 11 | Login barbero | POST | 200 | PASA |
| 12 | Me con token -> 200 | GET | 200 | PASA |
| 13 | Me sin token -> 401 | GET | 401 | PASA |
| 14 | Me con token inválido -> 401 | GET | 401 | PASA |
| 15 | Refresh token OK | POST | 200 | PASA |
| 16 | Refresh token inválido -> 401 | POST | 401 | PASA |
| 17 | Dashboard como barbero -> 200 | GET | 200 | PASA |
| 18 | Dashboard como cliente -> 403 | GET | 403 | PASA |
| 19 | Dashboard sin token -> 401 | GET | 401 | PASA |
| 20 | Perfil cliente /clientes/me/ | GET | 200 | PASA |
| 21 | Perfil barbero /barberos/me/ | GET | 200 | PASA |
| 22 | Cliente en /barberos/me/ -> 403/404 | GET | 403 | PASA |
| 23 | Notificaciones del cliente | GET | 200 | PASA |
| 24 | Notificaciones sin token -> 401 | GET | 401 | PASA |
| 25 | Pagos sin token -> 401 | GET | 401 | PASA |
| 26 | Método no permitido (DELETE /auth/login/) -> 405 | DELETE | 405 | PASA |
