# Informe de Accesibilidad — Barber Life (Sprint 4)

## 1. Alcance y método

Se auditaron las 11 pantallas principales (login, registro, inicio, solicitar turno, mis turnos, perfil de cliente, notificaciones, dashboard, gestión de turnos, catálogo y perfil de barbero), en escritorio (1440 px) y celular (390 px), contra la API real con datos `seed_demo`.

| Capa | Herramienta | Cómo |
|---|---|---|
| Automática | axe-core 4.x + Playwright (etiquetas wcag2a, wcag2aa, wcag21a, wcag21aa, wcag22aa y best-practice) | `e2e/tests/test_accesibilidad.py` (ACC-01..05) |
| Automática | Lighthouse 12, categoría Accesibilidad | Informes HTML/JSON en `docs/accesibilidad/lighthouse/` |
| Manual / semiautomática | Checklist mínimo de la consigna (teclado, formularios, contraste, imágenes, estructura, SPA, zoom/reflow) | Sección 4 |

## 2. Resultados antes y después

Violaciones axe (pantalla × viewport) y puntaje Lighthouse. "Antes" = `develop` sin correcciones; "después" = con las correcciones de este sprint.

| Pantalla | axe escritorio | axe celular | Lighthouse escritorio | Lighthouse celular (después) |
|---|---|---|---|---|
| Login | 2 → 0 | 2 → 0 | 100 → 100 | 100 |
| Registro | 2 → 0 | 2 → 0 | 100 → 100 | 100 |
| Inicio | 2 → 0 | 2 → 0 | 99 → 100 | 100 |
| Solicitar turno | 2 → 0 | 2 → 0 | 99 → 100 | 100 |
| Mis turnos | 2 → 0 | 2 → 0 | 99 → 100 | 100 |
| Perfil (cliente) | 2 → 0 | 2 → 0 | 99 → 100 | 100 |
| Notificaciones | 2 → 0 | 2 → 0 | 99 → 100 | 100 |
| Dashboard | 3 → 0 | 3 → 0 | 94 → 100 | 100 |
| Gestión de turnos | 3 → 0 | 3 → 0 | 95 → 100 | 100 |
| Catálogo | 3 → 0 | 3 → 0 | 94 → 100 | 100 |
| Perfil (barbero) | 3 → 0 | 3 → 0 | 94 → 100 | 100 |

**Total axe: 52 violaciones → 0** (22 corridas). **Lighthouse: 94–100 → 100** en las 11 pantallas. Los tests E2E de accesibilidad pasaron de **15 fallos de 33** a **33/33 en verde**, y los 2 tests de teclado sobre el diálogo (ACC-04 y ACC-05) fallaban antes y pasan después (**35/35** en total). El fallo "antes" quedó registrado con trace, video y captura en `docs/accesibilidad/evidencia-fallo-e2e/`: flujo login → abrir el perfil de un barbero → Esc, donde el diálogo no se cerraba (`test_acc_05`, A11Y-07).

## 3. Hallazgos y correcciones

| ID | Criterio WCAG | Sev. | Pantalla / componente | Problema | Corrección y justificación | Estado |
|---|---|---|---|---|---|---|
| A11Y-01 | 3.1.1 Idioma de la página (A) | Seria | Toda la app · `index.html` | `<html lang="en">` con contenido en español: el lector de pantalla pronuncia mal. | `lang="es"`. La interfaz está íntegramente en español. | Corregido |
| A11Y-02 | 2.4.2 Titulado de páginas (A) | Seria | Todas las rutas · `app.routes.ts` | Las 11 rutas comparten el título "Barber Life": no se distingue en qué vista se está (pestañas, historial, lector). | Propiedad `title` por ruta ("Mis turnos \| Barber Life", etc.). | Corregido |
| A11Y-03 | 1.3.1, 3.3.2, 4.1.2 (A) | Seria | Login · campos email y contraseña | Solo tienen placeholder, sin `<label>` ni `aria-label`: el placeholder desaparece al escribir y no es un nombre accesible fiable. | `aria-label` (mantiene el diseño del Figma, que no muestra etiqueta visible) + `autocomplete`. | Corregido |
| A11Y-04 | 3.3.1, 4.1.3 (AA) | Moderada | Login y registro · mensajes de error | Los errores de campo aparecen sin anunciarse ni asociarse al campo. | `role="alert"`, `aria-invalid` y `aria-describedby` hacia el mensaje. | Corregido |
| A11Y-05 | 1.4.3 Contraste mínimo (AA) | Seria | Barra superior · insignia de notificaciones | Texto blanco 10 px sobre `#ED4245`: **3.84:1** (mínimo 4.5:1). | Nuevo token `--color-bl-on-danger: #000` (**5.47:1**). La regla de la guía de estilos ya limitaba el rojo a fondos/íconos; el texto sobre rojo debe ser oscuro. | Corregido |
| A11Y-06 | 2.5.3 Etiqueta en el nombre (A) | Seria | Barra superior · campanita y avatar | El nombre accesible ("Notificaciones", "Menú de usuario") no contiene el texto visible ("3", "CR"): falla para control por voz. | Nombre dinámico: "Notificaciones, 3 sin leer" y "CR, menú de usuario"; la insignia queda `aria-hidden`. | Corregido |
| A11Y-07 | 2.1.2, 2.4.3 (A) | Seria | Inicio (modal de barbero) y Mis turnos (cancelar) | El foco queda detrás del modal, Esc no cierra y Tab escapa al fondo. | Directiva `blDialogFocus`: foco inicial dentro, Esc cierra, Tab cíclico y foco devuelto al disparador. | Corregido |
| A11Y-08 | 1.3.1 (A, best-practice) | Moderada | Login y registro | Sin landmark `<main>`; contenido fuera de landmarks. | `<main>` para el formulario y `<aside>` para el panel de presentación. | Corregido |
| A11Y-09 | 1.1.1 (A, best-practice) | Leve | Barra superior · logo | `alt="Barber Life"` repite el texto que lo acompaña. | Logo decorativo (`alt=""`) cuando va con el texto. | Corregido |
| A11Y-10 | 1.4.3 (AA) | Seria | Mis turnos · botón "Sí, cancelar turno" | Texto blanco sobre `#ED4245`: 3.84:1 (detectado por revisión manual del código; axe no lo ve porque el diálogo está cerrado). | Mismo token `--color-bl-on-danger`. | Corregido |
| A11Y-11 | 1.4.3 (AA) | Seria | Inicio · tarjeta con degradado | Texto blanco sobre degradado `accent-3 → accent`: entre **2.5:1 y 4.6:1** según la posición. Axe no puede medirlo (fondo degradado). | El degradado pasa a `accent → accent-2` (`.bl-accent-gradient` en `styles.css`): el texto blanco queda entre **4.61:1 y 6.42:1** en toda la tarjeta, sin cambiar el texto ni la paleta. | Corregido |
| A11Y-12 | 2.4.3 (A) | Moderada | SPA · cambio de ruta | No se gestiona el foco al navegar entre vistas. | `app.ts` mueve el foco al `<h1>` en cada `NavigationEnd` (salvo la primera carga). Verificado con NVDA y con el test `test_a11y_12`. | **Corregido** |
| A11Y-13 | 4.1.2 Nombre, función, valor (A) | Moderada | Solicitar turno · botones de servicio, barbero, día, hora y pago | Con NVDA, al elegir una opción solo se oye el nombre del botón: no se anuncia cuál quedó seleccionada (solo se ve por el borde). Detectado en el recorrido con NVDA. | `aria-pressed` en los botones de servicio, barbero, día, hora y pago. NVDA ahora anuncia "botón conmutador, pulsado / sin pulsar". Verificado con NVDA y con el test `test_a11y_13`. | **Corregido** |

Nota: los 13 hallazgos (A11Y-01 a A11Y-13) quedaron corregidos y verificados; A11Y-12 y A11Y-13 se detectaron en el recorrido manual con NVDA y se corrigieron el mismo día.

## 4. Checklist manual

| Ítem | Resultado | Evidencia |
|---|---|---|
| Teclado: Tab/Shift+Tab/Enter/Espacio/Esc operan toda la funcionalidad | Pasa (modales corregidos, A11Y-07) | Recorrido con Playwright (Tab) en login y test ACC-04 |
| Orden de foco lógico y foco visible | Pasa: botones y enlaces con contorno 2 px; campos con borde `accent` (3.6:1 contra el fondo) | Recorrido con Playwright (Tab) en login |
| Sin trampas de foco en modales/menús | Pasa tras A11Y-07 | Tests ACC-04 y ACC-05: foco dentro del modal y Esc lo cierra |
| Formularios: label/aria-label en cada campo | Pasa tras A11Y-03 | axe + revisión |
| Errores descritos en texto y anunciados | Pasa tras A11Y-04 | revisión |
| Contraste 4.5:1 / 3:1 | Pasa tras A11Y-10 y A11Y-11 | axe + cálculo manual |
| Imágenes: alt significativo / vacío en decorativas | Pasa (A11Y-09); fotos de barberos con `alt=""` | revisión |
| `lang="es"` en `index.html` | Pasa tras A11Y-01 | test ACC-02 |
| Un único `h1` por vista, sin saltos | Pasa (11/11 con un `h1`); en login/registro el panel de presentación usa `h2` antes del `h1` (menor) | script de encabezados |
| Landmarks header/nav/main | Pasa tras A11Y-08 (no hay `footer`: no hay contenido de pie) | axe |
| Botones y enlaces nativos | Pasa | revisión |
| SPA: título distinto por ruta | Pasa tras A11Y-02 | test ACC-02 |
| SPA: gestión del foco al navegar | Pasa tras A11Y-12 | `test_a11y_12`, NVDA |
| Zoom 200 % y reflow a 320 px | Pasa en las 11 pantallas (sin scroll horizontal) | test ACC-03 |
| Lector de pantalla (NVDA), un flujo crítico completo | Pasa: login → solicitar turno recorrido con NVDA + Chrome; se encontraron y corrigieron A11Y-12 y A11Y-13 (detalle abajo) | Visor de voz de NVDA, 14/10/2026 |

### Recorrido con NVDA (flujo: login → solicitar turno)
Lector de pantalla NVDA en Windows con Chrome, solo teclado; lo anunciado se tomó del Visor de voz de NVDA (cliente `seed_demo`, 14/10/2026).

| Paso | Qué se hizo | Lo que anunció NVDA | Resultado |
|---|---|---|---|
| 1 | Abrir `/login` | "Iniciar sesión \| Barber Life documento" → "Presentación de Barber Life, complementario región, gráfico Barber Life" → "encabezado nivel 2 Tu turno, sin vueltas." | Bien: título propio y landmarks (`aside`). El panel lateral abre con un `h2` antes del `h1` (menor). |
| 2 | Tab al campo email | "principal región" → "formulario región" → "Email edición, Ingresa tu email, en blanco, tiene autocompletado" | Bien: nombre, rol y autocompletado. |
| 3 | Enviar el formulario vacío | "alerta Ingresá un email válido." y "alerta La contraseña es obligatoria."; en cada campo: "entrada inválida, <mensaje>" | Bien: los errores se anuncian solos y quedan asociados al campo (A11Y-03/04). |
| 4 | Iniciar sesión | "Inicio \| Barber Life - Google Chrome ventana" → "Inicio \| Barber Life documento" → "Barbería y peluquería" | Anuncia el título nuevo, pero no mueve el foco al contenido ni lee el `h1` (A11Y-12). Tab recorre: "Solicitar turno botón", "Ver servicios enlace", "Solicitar botón" ×3 y "RORodrigo Rojas3 servicios botón". |
| 5 | Ir a Solicitar turno y recorrer la pantalla | "Solicitar turno \| Barber Life documento"; menú "Inicio / Mis turnos / Solicitar turno / Mi perfil / Notificaciones enlace", "CR, menú de usuario botón"; "Barba20 min$10.00 botón", "Coloración60 min$25.00 botón", "Corte de pelo30 min$15.00 botón", "RORodrigo Rojas$10Barba · 20 min botón", "Mié14 botón" …, "09:00 botón" … "18:30 botón", "Pagar en el local Abonás cuando llegás botón", "Mercado Pago Pagá online ahora botón" | Bien: todos los controles tienen nombre y rol. Observaciones: las iniciales del avatar ("RO") se leen junto al nombre; los botones de servicio, día y hora no indican cuál está elegido (sin estado "pulsado"). |
| 6 | Elegir todo y confirmar | Al elegir: "Barba20 min$10.00 botón", "RORodrigo Rojas$10Barba · 20 min botón", "Jue15 botón", "12:30 botón", "Pagar en el localAbonás cuando llegás botón" (sin indicar cuál queda elegido). Antes de elegir, "Confirmar turno botón, no disponible". Al confirmar: "15/10/2026 · 12:30" → "Te avisamos cuando la barbería confirme tu horario." → "Solicitar otro turno botón" | Bien: el resultado se anuncia (fecha, hora y mensaje) y ofrece "Solicitar otro turno". Falla: al elegir una opción NVDA no anuncia que quedó seleccionada (A11Y-13). |
| 7 | Repetir los pasos 4 a 6 tras los arreglos | Al entrar a Solicitar turno: "Solicitar turno, encabezado nivel 1". Al elegir: "Barba20 min$10.00, botón conmutador, pulsado", "RORodrigo Rojas$10Barba · 20 min, botón conmutador, pulsado", "Jue 15, botón conmutador, pulsado", "12:30, botón conmutador, pulsado", "Pagar en el local Abonás cuando llegás, botón conmutador, pulsado". Al reelegir, la opción anterior pasa a "sin pulsar". Al confirmar: "Confirmando…" | Bien: el foco llega al `h1` y NVDA anuncia qué opción quedó elegida (A11Y-12 y A11Y-13 corregidos). |

**Conclusión:** el flujo se puede recorrer completo con lector de pantalla: títulos, landmarks, nombres de campo y errores se anuncian bien. Durante el recorrido se detectaron dos fallos (foco al cambiar de ruta, A11Y-12, y estado de selección de los botones de servicio, barbero, día, hora y forma de pago, A11Y-13); se corrigieron y se volvió a recorrer el flujo con NVDA (paso 7).

## 5. Reproducir

```bash
docker compose up
docker compose exec backend python manage.py seed_demo
cd e2e && pip install -r requirements.txt && playwright install chromium
pytest tests/test_accesibilidad.py tests/test_accesibilidad_teclado.py
```
Lighthouse: Chrome DevTools → Lighthouse → Accesibilidad (modo Escritorio y Celular) sobre cada pantalla.
