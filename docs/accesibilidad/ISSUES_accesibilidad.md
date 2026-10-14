# Issues de accesibilidad (etiqueta `accesibilidad`)

Cada integrante carga los suyos en GitHub. Etiquetas: `accesibilidad` (+ `bug`). Milestone: Sprint 4 - Octubre 2026. Evidencia: informe, capturas de axe/Lighthouse y `test_accesibilidad.py`.

## A11Y-01 — `<html lang="en">` con contenido en español

- **Responsable (reporta y corrige):** Agustín Ceballos
- **Criterio WCAG:** 3.1.1 Idioma de la página (A)
- **Severidad:** Seria
- **Pantalla / componente:** Toda la app
- **Archivos:** `frontend/src/index.html`
- **Cómo se reproduce:** Abrir la app con un lector de pantalla: lee el español con pronunciación inglesa.
- **Corrección propuesta:** Poner `lang="es"`.

## A11Y-02 — Todas las rutas tienen el mismo título "Barber Life"

- **Responsable (reporta y corrige):** Agustín Ceballos
- **Criterio WCAG:** 2.4.2 Titulado de páginas (A)
- **Severidad:** Seria
- **Pantalla / componente:** Todas las rutas
- **Archivos:** `frontend/src/app/app.routes.ts`
- **Cómo se reproduce:** Navegar entre vistas: la pestaña siempre dice "Barber Life".
- **Corrección propuesta:** Agregar `title` a cada ruta.

## A11Y-03 — Campos del login sin etiqueta accesible

- **Responsable (reporta y corrige):** Pablo Peralta
- **Criterio WCAG:** 1.3.1, 3.3.2, 4.1.2 (A)
- **Severidad:** Seria
- **Pantalla / componente:** Login · email y contraseña
- **Archivos:** `login.component.html`
- **Cómo se reproduce:** Los inputs solo tienen `placeholder`; sin label ni aria-label.
- **Corrección propuesta:** `aria-label` + `autocomplete`.

## A11Y-04 — Errores de campo no anunciados ni asociados

- **Responsable (reporta y corrige):** Pablo Peralta
- **Criterio WCAG:** 3.3.1, 4.1.3 (AA)
- **Severidad:** Moderada
- **Pantalla / componente:** Login y registro
- **Archivos:** `login.component.html`, `register.component.html`
- **Cómo se reproduce:** Enviar el formulario con datos inválidos: el lector no anuncia el error.
- **Corrección propuesta:** `role="alert"`, `aria-invalid`, `aria-describedby`.

## A11Y-08 — Login y registro sin landmark `<main>`

- **Responsable (reporta y corrige):** Pablo Peralta
- **Criterio WCAG:** 1.3.1 (A, best-practice)
- **Severidad:** Moderada
- **Pantalla / componente:** Login y registro
- **Archivos:** `login.component.html`, `register.component.html`
- **Cómo se reproduce:** axe: `landmark-one-main` y `region`.
- **Corrección propuesta:** `<main>` para el formulario y `<aside>` para el panel.

## A11Y-05 — Insignia de notificaciones con contraste 3.84:1

- **Responsable (reporta y corrige):** Miguel Scaccia
- **Criterio WCAG:** 1.4.3 Contraste mínimo (AA)
- **Severidad:** Seria
- **Pantalla / componente:** Barra superior
- **Archivos:** `topbar.component.ts`, `styles.css`
- **Cómo se reproduce:** Texto blanco 10 px sobre `#ED4245`.
- **Corrección propuesta:** Token `--color-bl-on-danger: #000` (5.47:1).

## A11Y-06 — Nombre accesible no contiene el texto visible (campanita y avatar)

- **Responsable (reporta y corrige):** Miguel Scaccia
- **Criterio WCAG:** 2.5.3 Etiqueta en el nombre (A)
- **Severidad:** Seria
- **Pantalla / componente:** Barra superior
- **Archivos:** `topbar.component.ts`
- **Cómo se reproduce:** axe: `label-content-name-mismatch` en las 9 pantallas con sesión.
- **Corrección propuesta:** Nombre dinámico e insignia `aria-hidden`.

## A11Y-09 — Logo con `alt` que repite el texto

- **Responsable (reporta y corrige):** Miguel Scaccia
- **Criterio WCAG:** 1.1.1 (A, best-practice)
- **Severidad:** Leve
- **Pantalla / componente:** Barra superior
- **Archivos:** `logo.component.ts`, `topbar.component.ts`
- **Cómo se reproduce:** axe: `image-redundant-alt`.
- **Corrección propuesta:** Logo decorativo (`alt=""`) junto al texto.

## A11Y-07 — Modales sin gestión de foco, Esc ni trampa de Tab

- **Responsable (reporta y corrige):** Rodrigo Rojas
- **Criterio WCAG:** 2.1.2, 2.4.3 (A)
- **Severidad:** Seria
- **Pantalla / componente:** Inicio (modal de barbero), Mis turnos (cancelar)
- **Archivos:** `inicio.component.*`, `mis-turnos.component.*`
- **Cómo se reproduce:** Abrir el modal: el foco queda detrás; Esc no cierra; Tab sale al fondo.
- **Corrección propuesta:** Directiva `blDialogFocus` + `aria-label` del diálogo.

## A11Y-10 — Botón "Sí, cancelar turno" con contraste 3.84:1

- **Responsable (reporta y corrige):** Rodrigo Rojas
- **Criterio WCAG:** 1.4.3 (AA)
- **Severidad:** Seria
- **Pantalla / componente:** Mis turnos · diálogo
- **Archivos:** `mis-turnos.component.html`
- **Cómo se reproduce:** Texto blanco sobre `#ED4245`.
- **Corrección propuesta:** `text-bl-on-danger`.

## A11Y-11 — Texto blanco sobre degradado con contraste insuficiente

- **Responsable (reporta y corrige):** Ignacio Cantoni
- **Criterio WCAG:** 1.4.3 (AA)
- **Severidad:** Seria
- **Pantalla / componente:** Inicio · tarjeta con degradado
- **Archivos:** `styles.css` (`.bl-accent-gradient`), `inicio.component.html`
- **Cómo se reproduce:** Entre 2.5:1 y 4.6:1 según la posición. Axe no lo detecta.
- **Corrección propuesta:** Decisión de diseño: oscurecer el degradado o usar texto oscuro.

## A11Y-12 — No se gestiona el foco al navegar entre vistas

- **Responsable (reporta y corrige):** Ignacio Cantoni
- **Criterio WCAG:** 2.4.3 (A)
- **Severidad:** Moderada
- **Pantalla / componente:** SPA
- **Archivos:** `app.routes.ts` / `app.component`
- **Cómo se reproduce:** Al cambiar de ruta el foco no se mueve al contenido nuevo.
- **Corrección propuesta:** Mover el foco al `h1` en cada navegación.
