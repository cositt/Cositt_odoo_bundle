# Cositt Announcement Banner

## Qué hace

Muestra una barra de aviso fija en la parte superior del backend de
Odoo (mensaje + estilo info/éxito/aviso/urgente), configurable por
compañía desde Ajustes. Visible para todos los usuarios internos hasta
que la cierren (por sesión de navegador — no persiste el cierre).

## Problema que resuelve

Comunicar avisos internos (mantenimientos programados, cambios de
proceso, recordatorios puntuales) sin depender de email o Discuss, con
algo visible de inmediato al entrar al backend.

## Investigación previa (evitar duplicar trabajo de Odoo)

Se buscó en el core (Community + Enterprise) algo equivalente antes de
escribir código. Lo único que aparece con "announcement" es el snippet
`s_announcement_scroll` de `website` — un elemento decorativo para
páginas públicas del sitio web, sin relación con avisos internos del
backend. Sin solapamiento.

## Arquitectura

- **Config vía `session_info()`**: mismo patrón que
  `cositt_backend_accent`/`cositt_kanban_ribbon_theme` — el mensaje y
  estilo viajan una vez en el HTML inicial (`odoo.__session_info__`),
  cero RPC adicional. Sin `sudo()`: `res.company` ya es legible por
  cualquier usuario interno de fábrica.
- **Componente OWL propio**, registrado en `registry.category("main_components")`
  — el mismo mecanismo que usa el core para el `LoadingIndicator` o el
  `NotificationManager` — pero **solo cuando hay algo que mostrar**
  (`if (config) { registry... }`): evita un componente vacío montado
  en el 99% de las instalaciones donde el aviso está desactivado.
- **Por qué `position: fixed` + `padding-top` dinámico, y no reordenar
  el DOM**: el `MainComponentsContainer` que monta el componente se
  renderiza en `web.WebClient` **después** del `NavBar` y del
  `ActionContainer` (`web/static/src/webclient/webclient.xml`) — no hay
  forma de que aparezca "por encima" solo con el flujo normal del
  documento. Se fija arriba de todo con `position: fixed` y se mide su
  altura real con `ResizeObserver` (el mensaje puede ocupar 1 o varias
  líneas según el ancho de pantalla) para empujar `.o_web_client` hacia
  abajo exactamente esa distancia vía una custom property CSS
  (`--cositt-announcement-banner-height`), en vez de asumir una altura
  fija que dejaría un hueco o un solape con el navbar.
- **`z-index: 1030`**: por encima del navbar (sin z-index propio,
  `position: relative`), pero por debajo de `modal-backdrop` (1040) y
  `modal` (1050) de Bootstrap — un diálogo abierto debe seguir tapando
  el aviso, no al revés.
- **`t-esc` en un nodo de texto normal de OWL** (no en un `<style>`,
  a diferencia del bug de `cositt_login_background`) — el mensaje se
  autoescapa correctamente sin necesitar `Markup()`. El campo es de
  texto libre escrito por un admin (`base.group_system`), pero el
  escapado no depende de esa confianza: aplica igual aunque el mensaje
  contenga `<`, `>` o comillas.

## Bug HIGH real encontrado en code review (no en verificación manual inicial)

El primer diseño empujaba `.o_web_client` con `padding-top` (correcto
para navbar y contenido, ambos en flujo normal), pero no tocaba
`.o_notification_manager` — el gestor de toasts nativos de Odoo
(confirmaciones, errores...), que es un componente **hermano** del
banner dentro de `main_components`, no un descendiente de
`.o_web_client`. Su posición la fija
`web/static/src/core/notifications/notification.scss` como cálculo de
Sass **en tiempo de compilación** (`$o-navbar-height * 1.15`, 46px ×
1.15 ≈ 53px desde arriba), asumiendo que el navbar arranca en `y=0` —
deja de ser cierto en cuanto el banner está activo. Con el aviso
encendido, cualquier toast nativo (guardar, validación fallida...)
aparecía superpuesto sobre el navbar ya desplazado hacia abajo, en vez
de aparecer debajo de todo.

Encontrado por el agente de code review leyendo el SCSS real del core
dentro del contenedor (no una suposición) — verificado independientemente
contra el mismo archivo antes de aplicar el fix. **Fix**: sumar
`var(--cositt-announcement-banner-height)` al `top` de
`.o_notification_manager` cuando el banner está activo (mismo mecanismo
de custom property + clase marcador que ya usa el resto del módulo).

Confirmado en navegador real disparando un toast de verdad
(`env.services.notification.add(...)` vía consola, con el aviso activo):
antes del fix el toast quedaba pegado al borde superior sin relación con
el navbar desplazado; después aparece correctamente justo debajo de la
barra de navegación, sin solape. Un `ValidationError` de guardado (por
ejemplo, el propio validador de color hexadecimal de
`cositt_backend_accent`) se mostró aparte como **diálogo modal**, no como
toast — los diálogos ya usan un z-index de Bootstrap (1050/1055) por
encima del banner (1030), sin necesitar este ajuste.

## Dónde vive la configuración

- **Ajustes → Cositt - Aviso** (pestaña propia, mismo patrón que los
  demás módulos Cositt).
- Campos en `res.company`: `cositt_announcement_banner_enabled`
  (Boolean), `cositt_announcement_banner_message` (Char, máx. 300
  caracteres, validado por `@api.constrains`) y
  `cositt_announcement_banner_style` (Selection: info/éxito/aviso/urgente).

## Alcance y limitaciones

- Solo **backend** (`web.assets_backend`) — `/web/login`, el frontend y
  el portal no se ven afectados en absoluto (verificado con un test
  HTTP dedicado).
- Un único aviso activo por compañía, sin segmentación por grupo de
  usuarios ni fecha de expiración — alcance deliberadamente mínimo para
  la primera versión (ver backlog en el README raíz).
- El cierre del aviso es solo en memoria (estado del componente OWL):
  recargar la página o volver a entrar lo vuelve a mostrar. No usa
  `localStorage` ni ningún otro mecanismo de persistencia por usuario.

## Seguridad

- Sin modelo nuevo, sin ACL nueva: los campos viven en `res.company`,
  que ya restringe la escritura a `base.group_system` y permite lectura
  abierta a cualquier usuario interno — necesario para que todos reciban
  el aviso, no solo los administradores.
- Sin `sudo()` en ningún punto (verificado por su propio test
  `test_module_never_calls_sudo`).
- `session_info()` solo lee campos de `res.company` (nunca `ir.model` ni
  ningún otro modelo con ACL más restrictiva) — se revisó explícitamente
  contra el bug CRITICAL real que tuvo `cositt_kanban_ribbon_theme`
  (lectura de un campo de `ir.model` sin ACL para usuarios normales,
  que rompía el backend entero). Aquí no aplica esa clase de bug.

## Verificación manual realizada

Sin dependencias externas en este módulo. Dos rondas en navegador real.

**Primera** (antes del code review): activar el aviso desde Ajustes con
mensaje y estilo "Urgente" → banner rojo visible de inmediato, contenido
del backend empujado hacia abajo sin solape con el navbar; navegación
SPA a Contactos con el aviso todavía visible (persiste entre rutas, como
se espera de un componente en `main_components`); botón de cierre (×)
oculta el banner y retira el `padding-top` al instante, sin hueco
residual; ventana angosta (480×700, simulando móvil) sin solape con el
menú hamburguesa.

**Segunda** (tras el fix del bug HIGH de arriba): toast nativo disparado
de verdad con el aviso activo → aparece debajo del navbar desplazado,
sin solape (antes del fix quedaba pegado al borde superior real de la
pantalla); un `ValidationError` de guardado confirmado como diálogo
modal por encima del banner, sin cambios necesarios ahí. También se
probó el caso de un mensaje compuesto solo por espacios (fix del MEDIUM
de mensaje en blanco): con `cositt_announcement_banner_message = "   "`
y el aviso activado, `_cositt_get_announcement_banner_config()` devuelve
`False` — ningún banner vacío llega a `session_info()`.

Aviso desactivado en ambas rondas al terminar; suite completa
re-ejecutada después de cada exploración manual (lección ya aplicada en
otros módulos del proyecto: no asumir base de datos compartida limpia).
Base de datos dev limpia al cierre.

## Capturas

Ver [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).
