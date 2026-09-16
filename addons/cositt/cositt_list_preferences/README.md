# Cositt List Preferences

## Qué hace

En cualquier vista de lista con columnas opcionales (el icono de
"⚙" al final de la cabecera, que deja mostrar/ocultar columnas), la
elección se guarda ahora **en el servidor, por usuario**, además de en
el propio navegador. Cambia de dispositivo, borra los datos del
navegador o entra desde otro sitio: tus columnas siguen como las
dejaste.

## Investigación previa (qué guarda Odoo hoy, y qué no)

Antes de diseñar nada se investigó el código fuente del cliente web de
Odoo 19 (`web/static/src/views/list/`), como pedía el encargo:

- **Columnas opcionales**: se guardan hoy **solo en `localStorage`**
  del navegador (`list_renderer.js`, `computeOptionalActiveFields` /
  `saveOptionalActiveFields`), con una clave que **ni siquiera
  distingue usuario** (`optional_fields,<modelo>,<vista>,...`, sin
  `uid`) — dos personas que compartan navegador comparten la misma
  preferencia. Esta es la única pieza que de verdad encaja con "algo
  que hoy vive solo en el navegador y debería vivir en el servidor",
  así que es el único alcance de este módulo.
- **Ancho de columnas**: comprobado en `column_width_hook.js` — **no
  se guarda en ningún sitio**, ni en localStorage ni en el servidor. Es
  estado en memoria puro (`let columnWidths = null`), se recalcula
  desde cero cada vez que se abre la vista. Guardarlo sería construir
  una funcionalidad nueva de cero, no migrar algo existente — se
  decidió con el usuario dejarlo fuera de este MVP.
- **Orden de la lista**: tampoco se guarda en ningún sitio (aparte del
  mecanismo ya existente y completamente aparte de "Favoritos" /
  `ir.filters`, que este módulo no toca). Fuera de alcance por el mismo
  motivo que el ancho de columnas.

## Cómo funciona

- **Servidor**: un modelo simple, `cositt.list.column.preference`
  (`user_id` + `view_key` + `active_fields`, únicos por usuario+vista).
  `view_key` es exactamente el mismo identificador que ya construye
  Odoo en el cliente (modelo + vista + campo relacional si es una
  lista anidada + lista de campos) — no se inventa un esquema de
  claves nuevo. `active_fields` es el mismo CSV de nombres de campo que
  ya usa localStorage. Dos métodos (`cositt_get_active_fields`,
  `cositt_set_active_fields`), toda la lógica de negocio ahí, nada en
  el cliente más que lo imprescindible.
- **Cliente**: un único archivo (`list_renderer_patch.js`) que aplica
  `patch()` sobre `ListRenderer.prototype` — el mismo mecanismo que usa
  el propio Odoo para extender componentes estándar (ver
  `mail/chatter_patch.js`), no una plantilla reescrita ni un
  componente propio. Se sobrescriben exactamente los dos métodos que
  ya existían para esto (`computeOptionalActiveFields`,
  `saveOptionalActiveFields`), llamando siempre a la versión original
  primero: **localStorage sigue funcionando exactamente igual que
  antes**, este módulo solo añade una segunda fuente (el servidor) que
  tiene prioridad cuando responde a tiempo.
- El guardado en servidor va **debounced** (400ms): si activas/desactivas
  varias columnas seguidas, solo se manda una petición al final, no una
  por cada clic.
- La lectura del servidor ocurre en `onWillStart` (antes del primer
  pintado de la lista, igual que ya hace el propio Odoo para tasas de
  cambio en ese mismo archivo) — sin parpadeo de columnas incorrectas.

## Qué NO puede romper (comprobado, no solo esperado)

- **Solo se llama al servidor si la vista tiene columnas opcionales de
  verdad** (`archInfo.columns.some(c => c.optional)`) — la inmensa
  mayoría de listas no tienen ninguna, así que no añaden ninguna
  petición de red extra.
- **Cualquier fallo de la llamada al servidor** (sin red, sin permiso,
  vista todavía sin id...) se captura y se ignora: la lista sigue
  funcionando exactamente como sin este módulo, con el valor de
  localStorage de siempre.
- **Listas anidadas (one2many embebidos)**: la clave ya distingue este
  caso (`nestedKeyOptionalFieldsData` en el propio `createViewKey` de
  Odoo), así que se persisten igual, de forma independiente de la
  lista padre.
- **Listas editables**: no se toca nada de la edición inline, solo la
  visibilidad de columnas opcionales.
- **Vistas personalizadas por Studio**: el módulo no asume nada sobre
  qué campos existen — si un campo guardado ya no es opcional (o ya no
  existe) en el arch actual, simplemente se ignora, igual que ya pasa
  hoy con el valor de localStorage cuando cambia una vista.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde
Aplicaciones. Sin dependencias externas.

## Permisos

Cada usuario solo ve/gestiona sus propias preferencias
(`ir.rule` por `user_id`); los administradores (grupo "Ajustes") ven
todas, para poder revisar/depurar. Sin `sudo()` en ningún punto.
