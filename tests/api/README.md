# Tests de API con Postman y Newman (AUT-API)

Colecciones que validan el contrato de la API REST de Barber Life desde afuera: códigos HTTP, estructura de las respuestas, autenticación con JWT y permisos por rol (RBAC), con casos positivos y negativos. Complementan los tests de backend (`APITestCase`), que prueban la API desde adentro.

| Carpeta | Colección | Requests | Aserciones |
|---|---|---|---|
| `auth-rbac/` | Barber Life - AUT-API 1: Autenticación y RBAC | 26 | 37 |
| `catalogo-turnos/` | Barber Life - AUT-API 2: Catálogo y Turnos | 49 | 87 |

Cada carpeta contiene la colección (`*.postman_collection.json`), el entorno (`entorno.local.json`) y la evidencia de la última corrida: `reporte_newman.html`, `reporte_newman_junit.xml`, `resultado_newman.json` y `resultados.md` (tabla con el resultado de cada request).

## Requisitos previos

- La API levantada en `http://localhost:8000` con Docker Compose:
  ```bash
  docker compose up --build
  ```
- Los datos demo cargados (una sola vez):
  ```bash
  docker compose exec backend python manage.py seed_demo
  ```
  Las colecciones usan las cuentas del seed: `admin@barberlife.com` / `admin1234` y `barbero@barberlife.com` / `barbero1234`. Los clientes de prueba se crean durante la corrida.
- Node.js 18 o superior, y Newman con su reporter HTML:
  ```bash
  npm install -g newman newman-reporter-html
  ```

## Cómo correr Newman

Desde la raíz del repositorio:

```bash
# 1) Autenticación y RBAC
cd tests/api/auth-rbac
newman run AuthRBAC.postman_collection.json -e entorno.local.json \
  -r cli,html,junit,json \
  --reporter-html-export reporte_newman.html \
  --reporter-junit-export reporte_newman_junit.xml \
  --reporter-json-export resultado_newman.json

# 2) Catálogo y turnos
cd ../catalogo-turnos
newman run CatalogoTurnos.postman_collection.json -e entorno.local.json \
  -r cli,html,junit,json \
  --reporter-html-export reporte_newman.html \
  --reporter-junit-export reporte_newman_junit.xml \
  --reporter-json-export resultado_newman.json
```

Una corrida correcta termina con `failures: 0` en la tabla final de Newman.

> Las colecciones se pueden correr en cualquier orden, pero cada una debe correrse **completa**: los requests están encadenados (el setup guarda los tokens y los IDs que usan los siguientes).

## Variables del entorno

`entorno.local.json` define las variables que usan las colecciones:

| Variable | Valor por defecto | Para qué |
|---|---|---|
| `baseUrl` | `http://localhost:8000/api` | URL base de la API |
| `adminEmail` / `adminPass` | `admin@barberlife.com` / `admin1234` | Cuenta de administrador del seed |
| `barberoEmail` / `barberoPass` | `barbero@barberlife.com` / `barbero1234` | Cuenta de barbero del seed |
| `tokenInvalido` | `token.invalido.xxx` | Token falso para los casos de 401 |

Para probar contra otra URL, sobreescribí la variable sin editar el archivo:

```bash
newman run AuthRBAC.postman_collection.json -e entorno.local.json --env-var "baseUrl=https://mi-servidor/api"
```

## Cómo abrirlas en Postman

1. En Postman: *Import* → seleccioná la colección y `entorno.local.json`.
2. Elegí el entorno "Barber Life - local" arriba a la derecha.
3. Ejecutá la colección con *Run collection* (o cada request, de arriba hacia abajo).

## Qué cubre cada colección

- **Autenticación y RBAC:** registro (válido, email duplicado, contraseñas distintas, contraseña débil, email inválido), login de cliente, barbero y admin, login inválido, `me`, refresh de token, accesos sin token o con token inválido (401), acceso con el rol equivocado (403) a dashboard, perfiles, notificaciones y pagos, y método no permitido (405).
- **Catálogo y turnos:** CRUD de servicios, horarios y ofertas barbero-servicio con sus validaciones (400), reserva de turnos (éxito, solapamiento, fecha pasada, fuera de horario), mis turnos, agenda, cambio de estado, cancelación y bajas lógicas.

## Resultados

Última corrida: 13/10/2026 sobre `develop`, con los datos de `seed_demo`: **75 requests, 124 aserciones, 0 fallidas**. El detalle está en `resultados.md` de cada carpeta y los reportes completos en `reporte_newman.html`.

Estos resultados figuran en la Matriz de Trazabilidad (capa "API (Postman/Newman)") y en la página Testing de la Wiki.

## Notas

- Las colecciones no tienen credenciales reales: solo usan las cuentas del `seed_demo`, que existen únicamente en el entorno local.
- Si una corrida falla en el setup, revisá que el seed esté cargado y que no se haya cambiado la contraseña de las cuentas demo.
