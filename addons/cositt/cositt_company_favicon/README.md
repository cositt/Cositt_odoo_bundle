# Cositt Company Favicon

## Qué hace

Personaliza el favicon (icono de la pestaña del navegador) y el título
de la pestaña con una imagen PNG y un texto de marca propios, por
compañía — en todo el sitio: backend, `/web/login` y portal.

## Problema que resuelve

Con Odoo instalado tal cual, todas las pestañas del navegador muestran
el icono y el nombre genéricos de Odoo, sin importar cuántas apps
distintas tenga abiertas un usuario — difícil distinguir "el ERP" de
otras pestañas, y sin ningún rastro de marca propia.

## Arquitectura (investigada antes de escribir código)

- **`web.layout` ya declara `x_icon` y `title` como variables QWeb con
  fallback**: `<link ... t-att-href="x_icon or '/web/static/img/favicon.ico'"/>`
  y `<title t-esc="title or 'Odoo'"/>`. Hoy solo las rellena el
  mecanismo de apps PWA "scoped" (`/scoped_app_icon_png?app_id=...`).
  Reutilizarlas con un simple `t-set`, en vez de un xpath sobre el
  markup del `<head>`, es mucho más seguro — sin el riesgo de colisión
  con `web_enterprise`/`website` que sí afectó a
  `cositt_login_background` (ese caso necesitaba insertar markup
  NUEVO condicionado por ruta; este solo rellena un valor por
  defecto ya existente).
- **`t-value="x_icon or ..."` / `"title or ..."`, nunca al revés**: si
  otra ruta/controlador ya puso un título o icono más específico
  (`/scoped_app`, la página PWA "Añadir a la pantalla de inicio", que
  hace su propio `t-set` antes de que esta xpath corra), ese valor
  gana — este módulo solo rellena cuando la variable sigue sin
  definir. **Bug real encontrado en code review**: un primer intento
  tenía el orden invertido (`cositt_favicon_url or x_icon`), que da
  prioridad SIEMPRE a este módulo — reproducido en vivo contra
  `/scoped_app?app_id=mail`, dejaba el `<title>`/favicon de esa página
  pisados e inconsistentes con su propio `apple-touch-icon` (calculado
  aparte, no afectado). Corregido, con test de regresión
  (`test_scoped_app_title_and_icon_not_clobbered`).
- **El backend es una SPA que recalcula `document.title` en cada
  navegación** (`web/static/src/core/browser/title_service.js`,
  `updateTitle()` hace `document.title = parts.join(" - ") || "Odoo"`,
  ignorando el `<title>` servido por completo tras la carga inicial).
  El `<title>` server-side de arriba cubre `/web/login`, el portal y
  el primer parpadeo antes de que el JS arranque — pero para que el
  título de marca sobreviva a la navegación DENTRO del backend hace
  falta un patch JS sobre ese servicio (ver
  `company_favicon.js`): envuelve `setParts()` para que siempre incluya
  la marca como una parte más del título final
  (`"Inventario - Cositt ERP"` en vez de solo `"Inventario"`).
- **Solo PNG para el favicon**: formato recomendado para iconos
  modernos (transparencia real, sin pérdida). `.ico` no se admite:
  Pillow (usado por `fields.Image` para redimensionar) no lo decodifica
  de forma fiable en este build de Odoo — mismo tipo de hallazgo que el
  WEBP de `cositt_login_background`.

## Dónde vive la configuración

- **Ajustes → Cositt - Marca** (pestaña propia, mismo patrón que los
  demás módulos Cositt).
- Campos en `res.company`: `cositt_branding_enabled` (Boolean),
  `cositt_favicon_image` (Image, PNG, máx. 256×256/512 KB) y
  `cositt_browser_title` (Char, máx. 60 caracteres).

## Alcance y limitaciones

- Aplica en todo el sitio (backend, login, portal) — a diferencia de
  `cositt_login_background` (solo login) o `cositt_backend_accent`
  (solo backend), este módulo no restringe por ruta a propósito: un
  favicon/título de marca tiene sentido en todas partes por igual.
- Multiempresa: mismo límite ya documentado en
  `cositt_login_background` — un visitante anónimo de `/web/login`
  resuelve siempre a la compañía de `base.public_user`, no a una
  elegida en el momento del login.
- El texto del título del backend se AÑADE como una parte más
  (`"Vista - Marca"`), no reemplaza el nombre de la vista actual — así
  se sigue viendo qué pantalla está abierta, con la marca al final.

## Bug real encontrado en verificación manual (no en tests)

El patch de `titleService` inicialmente mezclaba la marca con
`{...parts, cositt_brand: brand}` en una sola llamada. JS conserva el
orden de INSERCIÓN de las claves de un objeto, y `setParts()` solo
actualiza el valor de una clave ya existente sin mover su posición —
como la llamada inicial (`service.setParts({})`, al arrancar, para
cubrir el Home Menu) insertaba `cositt_brand` como primera clave, se
quedaba ahí para siempre: el título salía "Cositt ERP - Inventory
Overview" en vez de "Inventory Overview - Cositt ERP". Corregido
borrando y reinsertando la clave en cada llamada, para que quede
siempre última. Verificado en navegador real navegando dentro del
backend (clic en menú "Operations" de Inventario, no solo carga
inicial) — el orden correcto solo se confirma con una navegación SPA
real, no con la primera carga de página.

**Nota operativa para verificación manual futura**: visitar
`/odoo/settings` en el mismo tab DESPUÉS de escribir la configuración
por RPC directo puede revertir los valores a un estado en caché del
formulario (observado una vez en esta sesión) — si se necesita
verificar tanto el panel de Ajustes como el comportamiento del
backend, capturar el panel de Ajustes PRIMERO o re-aplicar la
configuración por RPC después de visitarlo.

## Seguridad

- Sin modelo nuevo, sin ACL nueva: los campos viven en `res.company`,
  que ya restringe la escritura a `base.group_system`/ERP Manager y
  permite lectura abierta a cualquier usuario (incluido anónimo,
  necesario para que el favicon se sirva en `/web/login` sin sesión).
- Sin `sudo()` en ningún punto (verificado por su propio test
  `test_module_never_calls_sudo`).
- El favicon se valida por mimetype real del contenido decodificado
  (no por extensión de archivo) — mismo patrón que el resto de campos
  de imagen de este proyecto.

## Capturas

Ver [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).
