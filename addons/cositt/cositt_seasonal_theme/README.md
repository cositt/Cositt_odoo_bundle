# Cositt Seasonal Theme

## Qué hace

Icono temático en la barra de navegación del backend (Navidad, Feria,
Cumpleaños o Campaña personalizada) y, opcionalmente, partículas
decorativas animadas (copos, flores, velas, confeti de colores)
flotando sobre el backend — configurable por compañía, con rango de
fechas opcional para activar/desactivar solo.

## Problema que resuelve

Dar un toque festivo/de marca al backend en fechas señaladas
(Navidad, aniversario de la empresa, una feria concreta, una campaña
puntual) sin necesidad de instalar un theme completo ni tocar SCSS
cada vez — y sin tener que acordarse de apagarlo a mano: el rango de
fechas lo hace automáticamente.

## Arquitectura (investigada antes de escribir código)

- **¿Por qué un ítem de systray y no un elemento `position:fixed`
  propio?** Antes de elegir dónde vivía el icono, se investigó qué
  esquinas de la pantalla ya usa el core: `.o_loading_indicator`
  (el indicador de "Loading") vive fijo en la esquina **inferior
  derecha** con `z-index: $zindex-modal + 1`; `.o_notification_manager`
  (los toasts nativos) vive fijo en la esquina **superior derecha**,
  justo debajo del navbar; y el breadcrumb/botones de cada vista
  ocupan la izquierda justo debajo del navbar (visible en las capturas
  de `cositt_announcement_banner`). No queda ninguna esquina realmente
  libre — por eso el icono se registra como **ítem de systray**
  (`registry.category("systray")`, el mismo mecanismo que usan
  Mensajes/Actividades/Usuario del core): un lugar establecido,
  siempre en flujo normal, que nunca compite por espacio con nada de
  lo anterior.
- **Partículas 100% CSS, sin canvas ni bucle de JS por fotograma**: la
  posición/tiempo de cada partícula se calcula una única vez en
  `setup()` (`Math.random()`), y todo el movimiento real lo hace
  `@keyframes` de CSS. El componente solo se registra en
  `main_components` cuando hay tema activo Y el admin dejó las
  partículas encendidas — cero coste cuando está desactivado.
- **`z-index: 5`** para el overlay de partículas: muy por debajo de
  cualquier UI interactiva real (dropdowns 1000, fixed 1030, modales
  1050-1055, notificaciones 1055, indicador de carga 1056 — valores
  verificados contra el código fuente real de Bootstrap/Odoo dentro
  del contenedor). El contenedor y cada partícula llevan
  `pointer-events: none`: la decoración nunca puede interceptar un
  clic, pase lo que pase con el z-index.
- **`prefers-reduced-motion: reduce`** desactiva toda animación de
  partículas vía media query CSS — quien pide menos movimiento en su
  sistema operativo no debería tener que verla igual.
- **`fields.Date.context_today(self)`**, no `fields.Date.today()`,
  para el rango de fechas — respeta la zona horaria del usuario/
  compañía en vez de UTC crudo.
- **`session_info()` solo lee campos de `res.company`** (nunca
  `ir.model` ni otro modelo con ACL restrictiva) — se revisó
  explícitamente contra el bug CRITICAL real que tuvo
  `cositt_kanban_ribbon_theme` (lectura de un campo de `ir.model` sin
  ACL para usuarios normales, que rompía el backend entero). Aquí no
  aplica esa clase de bug.
- **`label` vía `t-att-title`** sobre un `<div>` normal (no un
  `<style>`, a diferencia del bug real de `cositt_login_background`):
  Owl fija atributos vía la API DOM estándar, que escapa
  correctamente — no hace falta `Markup()`.

## Temas y partículas

| Tema | Icono | Partículas |
|------|-------|------------|
| Navidad | 🎄 | Copos de nieve (❄️) cayendo |
| Feria | 🎪 | Flores variadas (🌸🌼🌻🌷) cayendo |
| Cumpleaños | 🎂 | Velas (🕯️) cayendo + destellos (🎉✨) apareciendo/desapareciendo |
| Campaña personalizada | 🎊 | Puntos de colores variados cayendo (sin emoji) |

Total de partículas acotado por tema (≤20) — "decoraciones ligeras",
a propósito.

## Dónde vive la configuración

- **Ajustes → Cositt - Decoración** (pestaña propia, mismo patrón que
  los demás módulos Cositt).
- Campos en `res.company`: `cositt_seasonal_theme_enabled` (Boolean),
  `cositt_seasonal_theme_kind` (Selection), `cositt_seasonal_theme_label`
  (Char, máx. 140 caracteres, validado por `@api.constrains`),
  `cositt_seasonal_theme_animation_enabled` (Boolean),
  `cositt_seasonal_theme_date_start`/`_date_end` (Date, opcionales,
  validados para que "Hasta" no sea anterior a "Desde").

## Hallazgos de code review corregidos

- **HIGH**: la clase de test `HttpCase` no reseteaba el estado de la
  compañía en `setUp()` (a diferencia de la clase `TransactionCase`,
  que sí lo hacía) — reproducido en vivo contra `cositt_plugins_dev`
  tras dejar el módulo activo en una verificación manual: un test
  fallaba por asumir compañía limpia. Mismo patrón ya visto en
  `cositt_kanban_ribbon_theme`/`cositt_announcement_banner`. Corregido
  con un `setUp()` idéntico al de la otra clase.
- **MEDIUM**: `cositt_seasonal_theme_label` no tenía límite de
  longitud del lado del servidor (solo `maxlength` en la vista,
  cliente) — a diferencia de los dos módulos hermanos con un campo de
  texto libre equivalente (`cositt_login_background`,
  `cositt_announcement_banner`), que sí lo validan con
  `@api.constrains`. Corregido para seguir el mismo patrón.
- **MEDIUM**: faltaban tests de los bordes exactos del rango de fechas
  (`today == date_start`, `today == date_end`) — la lógica ya era
  correcta (ambos extremos inclusive), pero no estaba verificada.
  Añadidos.
- **LOW**: el icono del systray solo tenía `title` como nombre
  accesible (no fiable para lectores de pantalla). Añadido
  `role="img"` + `aria-label`.
- **LOW**: `THEME_KINDS` (Python) y `SEASONAL_THEMES` (JS) son dos
  fuentes de verdad sin chequeo de paridad automático — documentado
  con comentarios cruzados en ambos archivos para que quien agregue un
  tema nuevo no se olvide del otro lado.

## Alcance y limitaciones

- Solo **backend** (`web.assets_backend`) — `/web/login`, el frontend y
  el portal no se ven afectados en absoluto (verificado con un test
  HTTP dedicado).
- Un único tema activo por compañía, sin combinar varios a la vez.
- El icono es puramente informativo (tooltip al pasar el ratón); no
  tiene acción de clic.

## Seguridad

- Sin modelo nuevo, sin ACL nueva: los campos viven en `res.company`,
  que ya restringe la escritura a `base.group_system` y permite
  lectura abierta a cualquier usuario interno.
- Sin `sudo()` en ningún punto (verificado por su propio test
  `test_module_never_calls_sudo`).

## Verificación manual realizada

En navegador real: activar la decoración con tema Navidad → icono 🎄
en el systray junto a Actividades, copos de nieve visibles flotando
sobre Ajustes y sobre Contactos (confirmado tanto visualmente como
contando los nodos `.o_cositt_seasonal_theme_particle` en el DOM).
Cambiado a tema Cumpleaños con mensaje personalizado → icono 🎂 con el
tooltip correcto (confirmado leyendo `title`/`textContent` del
elemento real), velas cayendo + destellos apareciendo/desapareciendo
visibles a la vez en Contactos. Rango de fechas verificado de extremo
a extremo escribiendo una fecha "Hasta" en el pasado directamente
sobre la compañía real: `_cositt_get_seasonal_theme_config()` devolvió
`False` y, tras recargar el backend, tanto el icono como las
partículas desaparecieron del DOM — confirmado que el rango de fechas
no es solo lógica Python aislada, sino que corta el flujo completo
hasta la UI. Estado reseteado a los valores por defecto al terminar;
suite completa (29 tests, 25 efectivos) vuelta a correr después de
cada ronda de exploración manual.

## Capturas

Ver [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).
