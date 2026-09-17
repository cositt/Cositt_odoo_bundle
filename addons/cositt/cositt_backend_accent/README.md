# Cositt Backend Accent

## Qué hace

Aplica un color de acento configurable (por compañía) a botones primarios,
checkboxes/radios y al ítem de menú activo del backend de Odoo — sin
instalar un theme completo.

## Problema que resuelve

Muchas empresas quieren que el backend combine con su color corporativo
sin pagar/mantener un theme completo de Odoo (que suele tocar mucho más
que el color: tipografías, espaciados, iconografía). Este módulo cambia
solo el acento — botones primarios y unos pocos elementos "activos" — y
nada más.

## Arquitectura (investigada antes de escribir código)

- **`$o-brand-primary` es una variable Sass**, compilada de forma fija
  dentro de `web.assets_backend.min.css` — no existe forma de cambiarla
  en tiempo de ejecución sin recompilar el bundle (o sin depender de
  `web_editor`/Website Theme, fuera de alcance de este módulo). Se
  descartó ese camino tras leer el código fuente
  (`web/static/src/scss/primary_variables.scss`).
- **Bootstrap 5 sí expone custom properties CSS en tiempo de
  ejecución**, pero no en `:root` para los botones: el mixin
  `button-variant()` (`bootstrap/scss/mixins/_buttons.scss`) declara
  variables por componente **dentro de la propia regla `.btn-primary`**
  (`--btn-bg`, `--btn-border-color`, `--btn-hover-bg`, etc.), y la clase
  base `.btn` ya las consume (`background-color: var(--btn-bg)`). **Ojo
  con el nombre exacto**: no llevan el prefijo estándar `--bs-` de
  Bootstrap — Odoo compila su propio fork con `$prefix` vacío,
  confirmado leyendo el CSS real servido por el navegador
  (`.btn-primary { --btn-bg: #714B67; ... }`, nunca `--bs-btn-bg`). Un
  primer intento con `--bs-btn-bg` no cambiaba nada (la variable
  simplemente no existe en este build) — detectado en verificación
  manual, no en el código fuente de Bootstrap solo. Este módulo no toca
  `background-color` directamente: reasigna esas mismas custom
  properties (con el prefijo correcto) dentro de `.btn-primary` (ver
  `backend_accent.scss`), heredando automáticamente el resto del
  comportamiento de Bootstrap (focus, disabled, etc. sin reescribirlo).
- **El ítem de menú activo del navbar YA es una custom property con
  fallback**: `--NavBar-entry-backgroundColor--active` y
  `--NavBar-entry-color--active` se consumen con
  `var(--NavBar-entry-*, fallback)` directamente en
  `web/static/src/webclient/navbar/navbar.scss`.
- **Checkboxes/radios usan `accent-color`**, una propiedad CSS nativa
  del navegador (sin necesidad de ningún framework ni JS adicional).

## Cómo se aplica (cero recompilación de SCSS core)

- `session_info()` (`models/ir_http.py`) inyecta el color ya validado,
  solo cuando el interruptor está activo y hay un color elegido — mismo
  patrón que `cositt_home_wallpaper`, `cositt_login_background` y
  `cositt_kanban_ribbon_theme`.
- `static/src/backend_accent/backend_accent.js` lee ese valor al
  arrancar el webclient y, SOLO si hay color, añade la clase
  `o_cositt_backend_accent_active` a `<html>` y hace
  `document.documentElement.style.setProperty('--cositt-backend-accent', color)`
  — una sola vez, sin RPC.
- `backend_accent.scss` envuelve TODAS sus reglas bajo
  `.o_cositt_backend_accent_active` — ver el bug real de abajo para el
  porqué de la clase marcador (no basta con "var() sin fallback").

## Bug CRITICAL real encontrado en verificación manual (no en tests ni en el primer code review)

El primer diseño no usaba la clase marcador: las reglas vivían sueltas
(`.btn-primary { --btn-bg: var(--cositt-backend-accent); ... }`,
`:root { --NavBar-entry-backgroundColor--active: var(...); ... }`),
confiando en el mismo mecanismo "var() sin fallback = inerte" que
`cositt_login_background` usa para su color de fondo. **Ese mecanismo
NO es seguro aquí**, y de hecho tampoco lo era del todo en
`cositt_login_background` (bug hermano corregido en la misma sesión,
ver el README de ese módulo) — la diferencia es sutil:

- Funciona bien cuando la regla afecta una propiedad NORMAL
  directamente (`background-color: var(--x)`): si `--x` no está
  definida, esa declaración concreta queda inválida y el navegador
  actúa como si no existiera, dejando pasar la de menor especificidad.
- **No funciona** cuando se reasigna una custom property de OTRO
  componente a una variable propia (`--btn-bg: var(--cositt-backend-accent)`,
  donde `--btn-bg` la consume luego `.btn` vía `background-color:
  var(--btn-bg)`, sin fallback en ningún punto). La cascada decide qué
  declaración de `--btn-bg` "gana" (la de este módulo, por cargarse
  después) **antes** de comprobar si su valor es válido. Si resulta
  inválida, `--btn-bg` no "cae de vuelta" a la declaración de Bootstrap
  que perdió esa cascada — queda "garantizado inválida", y
  `background-color` (que la consume sin fallback) cae a su valor
  inicial: `transparent`.

Resultado real, reproducido en navegador: con el módulo instalado y
**desactivado** (el estado por defecto de cualquier instalación nueva),
todos los botones primarios del backend entero quedaban invisibles —
justo lo contrario de "cero cambio visual sin configurar".

**Segundo bug relacionado (HIGH)**: incluso arreglando lo anterior,
`--NavBar-entry-backgroundColor--active`/`--NavBar-entry-color--active`
fijadas en `:root` nunca llegaban a aplicarse en este entorno concreto,
porque `web_enterprise` (instalado en este proyecto) fija esas mismas
variables con **valores fijos** directamente sobre `.o_main_navbar`
(`web_enterprise/static/src/webclient/navbar/navbar.scss`,
incondicional). Un elemento siempre gana sobre `:root` para esa
variable, sin importar el orden de carga de los bundles — mismo tipo
de bug ya documentado en `cositt_login_background`
("`web_enterprise` pisaba el fondo"), no aplicado aquí a la primera.

**Fix**: envolver todas las reglas de `backend_accent.scss` bajo la
clase marcador `.o_cositt_backend_accent_active` (añadida por JS solo
cuando hay color configurado) — así, desactivado, la regla entera no
existe para el navegador, no solo su valor; y anclar el navbar a
`.o_cositt_backend_accent_active .o_main_navbar` en vez de `:root`, para
ganar la pelea de especificidad contra `web_enterprise` de verdad.
Verificado de nuevo en navegador real tras el fix: botones normales por
defecto, verdes cuando se configura, y la barra del ítem activo de
Ajustes también en verde.

## Dónde vive la configuración

- **Ajustes → Cositt - Backend** (pestaña propia, mismo patrón que los
  demás módulos Cositt — independiente, instalable por separado).
- Campos en `res.company`: `cositt_backend_accent_enabled` (Boolean) y
  `cositt_backend_accent_color` (Char, `#rrggbb`, validado con el mismo
  regex ya usado en `cositt_login_background`/`cositt_home_wallpaper`).

## Alcance y limitaciones

- Solo **backend** (`web.assets_backend`) — `/web/login`, el frontend y
  el portal no se ven afectados en absoluto (verificado con un test
  HTTP dedicado).
- Solo botones primarios, checkboxes/radios y el ítem de menú activo —
  no toca botones secundarios, links, badges, ni ningún otro color de
  la paleta. Alcance deliberadamente acotado (ver backlog en el README
  raíz, ítem #6).
- Sin hover/active con sombreado automático (Bootstrap normalmente
  aclara/oscurece el color en hover): este módulo fija el mismo color
  plano en hover/active por simplicidad — una mejora futura podría
  calcular esos tonos en Python antes de inyectar el color.
- Sin recálculo de contraste del texto: el texto de los botones
  primarios sigue blanco (fijado en tiempo de compilación por
  Bootstrap contra el morado por defecto de Odoo) — un acento muy claro
  puede dejar el texto poco legible. Documentado en el `help` del campo
  `cositt_backend_accent_color`.

## Seguridad

- Sin modelo nuevo, sin ACL nueva: los dos campos viven en
  `res.company`, que ya restringe la escritura a
  `base.group_system`/ERP Manager y permite lectura abierta a
  cualquier usuario interno — necesario para que cualquiera que abra el
  backend reciba el color, no solo los administradores.
- Sin `sudo()` en ningún punto (verificado por su propio test
  `test_module_never_calls_sudo`).
- El color se valida contra un formato hexadecimal estricto
  (`#rrggbb`) antes de guardarse.

## Verificación manual realizada

Dos rondas. **Primera** (con el bug CRITICAL/HIGH de arriba aún sin
corregir): color de acento verde (`#0e9f6e`) aplicado en navegador
real — botón "Open" de Inventario, botón "New" de Contactos, checkbox
de Contactos y la barra del ítem activo de Ajustes, todos en verde. El
estado desactivado no se verificó en esa ronda — code review posterior
señaló que justo ese caso rompía todo, confirmado después contra el
backend real: botón "Open" completamente transparente con el módulo
recién instalado y sin tocar Ajustes.

**Segunda** (tras el fix): estado por defecto confirmado normal (botón
"Open" en el morado nativo de Odoo, sin rastro del módulo), estado
configurado reconfirmado en verde incluyendo ahora también la barra del
ítem activo de Ajustes (antes no cambiaba de color por el pisado de
`web_enterprise`, ver arriba). `/web/login` confirmado sin ningún
rastro del módulo (ni la variable CSS ni el JS) — HTTP real, no solo
lectura de código. Datos de prueba (color de acento) revertidos a
desactivado después. 14/14 tests en ambas rondas.

## Capturas

Ver [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).
