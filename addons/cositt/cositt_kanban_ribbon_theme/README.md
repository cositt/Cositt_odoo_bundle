# Cositt Kanban Ribbon Theme

## Qué hace

Añade un indicador de color a las tarjetas kanban de los modelos que
el administrador elija, usando un campo Integer que ya tenga ese
modelo — típicamente el mismo campo `color` que ya usa el selector de
color nativo de Odoo ("Establecer color" en el menú de cada tarjeta).
Tres estilos a elegir por regla (campo `style`):

- **Ribbon** (por defecto): banda triangular en la esquina superior
  derecha — el diseño original del módulo.
- **Borde izquierdo**: banda sólida de 4px pegada al lado izquierdo de
  la tarjeta, más discreta.
- **Punto**: círculo pequeño en la esquina superior derecha.

Los tres reutilizan exactamente la misma paleta de 12 colores nativa
de Odoo — el estilo solo cambia la forma, nunca los colores
disponibles ni el mecanismo de configuración.

## Problema que resuelve

Muchos modelos ya guardan un color por registro (`color`, Integer
0-11) pero la vista kanban estándar solo lo muestra como un borde
lateral fino, poco visible. Este módulo lo convierte en un ribbon más
prominente, para los modelos que el administrador elija — sin crear un
theme completo ni tocar ninguna vista kanban existente.

## Arquitectura (investigada antes de escribir código)

- **Reutiliza la paleta nativa, no inventa colores.** `$o-colors`
  (`web/static/src/scss/secondary_variables.scss`, 12 colores, cargado
  en `web.assets_backend` antes que el SCSS de este módulo) es la MISMA
  lista que usa el selector de color nativo de Odoo
  (`web/static/src/core/colorlist/colorlist.scss`, clases
  `o_colorlist_item_color_N`). El ribbon reutiliza esas clases
  directamente — combina siempre con el resto de la UI. `$o-colors` NO
  se redefine en modo oscuro (comprobado leyendo el código fuente): la
  consistencia viene de que el propio indicador nativo de kanban
  (`o_kanban_color_N`) tampoco lo ajusta, así que este módulo sigue el
  mismo criterio que el core, no uno propio.
- **Un único `patch()` sobre `KanbanRecord.getRecordClasses()`**
  (`@web/views/kanban/kanban_record`), no una plantilla OWL heredada:
  es la misma función que el propio core ya usa para añadir
  `o_kanban_color_N` cuando el arch declara `card_color_field` — reusar
  una función ya pensada para esto es más estable ante cambios de
  versión que heredar markup. **Hallazgo real verificado en el código
  fuente antes de escribir el patch**: `getRecordClasses()` devuelve un
  **string** ya unido (`classes.join(" ")`), no un array — el patch
  concatena texto, no hace `.push()`.
- **Cero RPC por vista kanban abierta**: la lista de modelos
  configurados viaja una vez en `session_info()` (mismo patrón que
  `cositt_home_wallpaper` y `cositt_login_background`).

## Bug real encontrado y corregido en code review (HIGH)

El primer diseño leía `rule.model_id.model` directamente dentro de
`_cositt_get_active_ribbon_rules()`, invocada desde `session_info()`
para CUALQUIER usuario en cada carga del backend. `model_id.model` es
un campo de OTRO modelo (`ir.model`) — leerlo dispara una comprobación
de ACL real sobre `ir.model`, y el ACL base de Odoo (`base/security/
ir.model.access.csv`) da **cero acceso** a `ir.model` para
`base.group_user` (usuarios internos normales, no administradores).

Resultado: en cuanto un administrador activaba una sola regla,
`session_info()` reventaba con `AccessError` para todo usuario no-admin
— **tumbaba `/odoo` entero para ellos, no solo el kanban**. Reproducido
de verdad contra este mismo `cositt_plugins_dev` antes de corregirlo.

Fix: campo `model_name` (`related="model_id.model", store=True`) en
`cositt.kanban.ribbon.rule` — el nombre técnico se calcula UNA vez
(cuando escribe un administrador, que sí tiene acceso a `ir.model`) y
queda guardado como `Char` normal en el propio modelo de la regla, cuyo
ACL de lectura ya está abierto a `base.group_user`. `session_info()`
lee `model_name`, nunca `model_id.model` — sin necesitar `sudo()`.
Test de regresión: `test_ordinary_user_can_compute_active_rules_without_access_error`
(nivel método) y `test_backend_session_info_does_not_500_for_ordinary_user`
(HTTP real, con un usuario interno nuevo, no admin).

## Otros hallazgos del review

- **Índice de color negativo** (MEDIUM): `getColorIndex()` del core
  usa `%` nativo de JS, que conserva el signo del dividendo — un
  `color_field_name` que apunte a un Integer legítimamente negativo
  daría una clase como `o_colorlist_item_color_-3`, que no coincide con
  nada del SCSS (ribbon invisible en vez de un color real). Corregido
  normalizando a un módulo verdadero en el JS.
- **Aislamiento de tests** (MEDIUM): varios tests asumían una base de
  datos "limpia" (`search([])` sin filtrar) — en un entorno de
  desarrollo compartido con verificación manual, eso rompía tests con
  datos de sesiones anteriores. Corregido: los tests ahora trabajan
  sobre el recordset propio de cada registro creado, no sobre
  `search([])`.
- **Alcance no garantizado por la vista** (documentado, no "arreglado"
  — ver Limitaciones): si la vista kanban del modelo elegido no incluye
  el campo de color entre los que carga, Odoo no lo trae al navegador y
  el ribbon simplemente no aparece, sin ningún error.

## Configuración

**Ajustes → Técnico → Ribbon de kanban (Cositt)** (requiere modo
desarrollador, mismo patrón que `cositt_smart_attachment_name`):

1. Elegí el modelo (ej. "Task" para `project.task`).
2. Dejá "color" como campo (o poné otro Integer del modelo).
3. Elegí el estilo (Ribbon / Borde izquierdo / Punto) — Ribbon por
   defecto, mismo comportamiento que antes de que existiera este campo.
4. Guardá. Las tarjetas kanban de ese modelo con un color ya elegido
   (vía el selector nativo "Establecer color") mostrarán el indicador
   con la forma configurada.

Un solo administrador puede crear/editar/borrar reglas
(`base.group_system`); cualquier usuario interno puede leerlas
(`base.group_user`, solo lectura) — necesario para que el ribbon se
pinte en el navegador de cualquiera, no solo del admin.

## Seguridad

- Sin modelo de datos nuevo expuesto más allá de `model_id` (nombre
  técnico de modelo), `color_field_name` (nombre de campo) y `style`
  (uno de tres valores fijos de un Selection) — nada sensible, y ya
  visible para cualquier usuario interno vía inspector del navegador en
  cualquier instalación de Odoo. `style` sigue el mismo ACL que el
  resto de campos de la regla (lectura abierta a `base.group_user`,
  escritura solo `base.group_system`) — no necesitó tocar
  `security/ir.model.access.csv`, es un campo más del mismo modelo, no
  uno con `groups=` propio.
- Sin `sudo()` en ningún punto (verificado por su propio test
  `test_module_never_calls_sudo`) — ver el bug HIGH de arriba sobre por
  qué esto exigió denormalizar `model_name` en vez de simplemente
  envolver la lectura en `sudo()`.

## Limitaciones

- El campo de color debe estar entre los que la vista kanban de destino
  carga (aunque sea oculto); si ninguna vista lo referencia, el ribbon
  no aparece, sin aviso — documentado en la ayuda del propio formulario
  de la regla.
- Si el campo se elimina del modelo después de crear la regla (Studio,
  actualización), la regla queda inactiva en la práctica de la misma
  forma silenciosa — revisar esta lista tras cambios grandes de campos.
- Un único color por registro (el que ya usa el selector nativo), no
  reglas de color condicionales por valor de otros campos.

## Capturas

Ver [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf) — capturas
reales: formulario de regla configurado sobre `project.task`, tarjeta
con ribbon aplicado tras usar el selector de color nativo, y un kanban
sin regla configurada (Inventario) sin ningún cambio visual.

## Verificación manual realizada

Regla real creada para `project.task`, color asignado a una tarea de
prueba, ribbon visible con el color correcto en navegador real (no
solo en tests). Kanban de Inventario (sin regla) confirmado sin
cambios. 0 errores en consola JS. Datos de prueba (proyecto, tarea,
regla) borrados después — base dev limpia. 16/16 tests (incluye
regresión HTTP real del bug HIGH con un usuario interno no-admin).

### Ronda de estilos (border + dot)

Code review (1 agente dedicado) sin CRITICAL/HIGH. Confirmó que no hay
regresión del bug HIGH original (`_cositt_get_active_ribbon_rules()`
sigue leyendo solo `model_name`, nunca `model_id.model`), que `style`
hereda el mismo ACL del resto de campos de la regla sin tocar
`security/ir.model.access.csv`, y que ningún otro módulo del repo
depende de la forma antigua (string plano) de
`session.cositt_kanban_ribbon_rules` — grep del repo entero, cero
coincidencias fuera de este módulo.

**Bug real encontrado en verificación manual, no en tests ni en
review** (mismo patrón repetido ya varias veces en este proyecto — ver
CLAUDE.md): el estilo "dot" se diseñó inicialmente en la esquina
superior derecha (`top:4px; right:4px`), igual que el ribbon. En
navegador real, al pasar el ratón sobre la tarjeta, el menú contextual
nativo "⋮" de kanban aparece exactamente en esa misma esquina y tapa el
punto. Ningún test automatizado lo detecta porque ninguno renderiza
CSS real ni simula `:hover`. Corregido moviendo el punto a la esquina
superior **izquierda** (`top:4px; left:4px`) — verificado en navegador
que ahí no choca con nada (el thin native color strip de
`project.task`, si lo hay, vive pegado a `x=0`, y el punto queda
desplazado 4px de ese borde).

También verificado visualmente: el borde izquierdo de 4px (estilo
"border") no choca con el border-radius/sombra nativos de la tarjeta
kanban — queda limpio, y "border"/"ribbon"/"dot" se probaron los tres
por separado sobre las mismas dos tareas de prueba (colores real de la
paleta nativa, no simulados). 18/18 tests (22 aserciones). Datos de
prueba (proyecto, 2 tareas, regla) borrados después — base dev limpia.
