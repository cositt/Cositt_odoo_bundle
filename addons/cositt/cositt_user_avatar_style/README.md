# Cositt User Avatar Style

## Qué hace

Odoo ya genera automáticamente un avatar con iniciales y color de fondo
para cualquier contacto/empleado (o cualquier registro que use el
mecanismo `avatar.mixin` del core) sin foto propia — pero elige el
color al azar (una función hash sobre el nombre), sin relación con la
identidad visual de la empresa. Este módulo reemplaza ESE color
aleatorio por uno elegido de una paleta de marca configurable por
compañía: cada persona sigue teniendo siempre el mismo color
(determinista por su nombre, como ya hace Odoo), pero ahora siempre
dentro de los colores que la empresa elija.

## Investigación previa (evitar reinventar lo que el core ya hace)

Antes de escribir código se investigó si "avatares con iniciales" ya
era una funcionalidad de Odoo, y lo es: `odoo/addons/base/models/
avatar_mixin.py` (`avatar.mixin`, heredado por `res.partner`,
`hr.employee` y otros modelos) ya genera un SVG con la inicial del
nombre sobre un color `hsl(...)` calculado con un hash — confirmado
viendo las propias capturas de este proyecto (los contactos de la base
dev ya mostraban iniciales de colores antes de instalar este módulo).
No hay un hueco real para "contactos normales sin avatar" — el hueco
real (direcciones hijas tipo Factura/Envío, contactos de portal) es
marginal y no vale la pena perseguir. El pedido genuino, tras
consultarlo, es **"estilo uniforme"** en el sentido de identidad de
marca: mismos colores en todos los avatares generados, no el arcoíris
aleatorio de Odoo.

## Arquitectura

- **El override vive en `avatar.mixin` mismo**, no en `res.partner` ni
  en ningún modelo concreto — así aplica automáticamente a cualquier
  modelo que use el mixin (Contactos, Empleados, y cualquier otro
  módulo instalado que lo use en el futuro), sin tener que tocar cada
  modelo uno por uno.
- **Solo se cambia `_avatar_generate_svg()`** (qué color usar), nunca
  la estructura del SVG ni el resto del mecanismo (cuándo generar un
  avatar vs. usar la foto real, cuándo cae al placeholder gris) — esa
  lógica sigue siendo 100% la del core, sin tocar.
- **Selección de color determinista**: mismo hash (`sha512` sobre
  nombre + fecha de creación, igual seed que usa el core) módulo la
  cantidad de colores de la paleta — la misma persona obtiene siempre
  el mismo color de la lista, no uno al azar en cada carga.
- **Sin JS, sin `session_info()`**: a diferencia de los módulos
  hermanos visuales de este proyecto, este es 100% servidor — el color
  se decide en el momento de generar el SVG de cada avatar (un campo
  `Image` computado, no almacenado, recalculado en cada lectura), no
  hay nada que viajar al cliente vía sesión.

## Bug real encontrado en mi propio testing (no en code review)

Los campos `avatar_1920/1024/512/256/128` de `avatar.mixin` son
computados pero **no declaran depender de la compañía activa** — Odoo
cachea su valor por registro sin distinguir bajo qué compañía se
calculó, a menos que el método `compute=` lo declare explícitamente
con `@api.depends_context("company")`. Sin eso, un mismo registro
consultado con `partner.with_company(otra_compañía)` dentro de la
misma transacción devolvía el color de la paleta de la compañía
ANTERIOR (cacheado), no la nueva — reproducido con un test real
(`test_avatar_color_depends_on_active_company_of_viewer`) que fallaba
antes del fix. Corregido redeclarando los 5 métodos
`_compute_avatar_*` con `@api.depends_context("company")` (patrón
usado por el propio core en varios sitios, ej.
`res_partner.py::_compute_vat_label`).

## Dónde vive la configuración

- **Ajustes → Cositt - Avatares** (pestaña propia).
- Campos en `res.company`: `cositt_avatar_style_enabled` (Boolean) y
  `cositt_avatar_style_palette` (Char, colores hexadecimales
  `#rrggbb` separados por coma, validados por `@api.constrains` —
  rechaza el guardado completo si un solo color es inválido, sin
  filtrar en silencio).

## Alcance y limitaciones

- Solo afecta a registros **sin foto propia** — quien ya tiene una
  imagen subida no se ve afectado en absoluto.
- El color depende de la **compañía activa de quien mira** el avatar
  (`env.company`), no de la compañía dueña del contacto — mismo
  comportamiento que otros campos `company_dependent` del core (ej.
  `_compute_vat_label`). Documentado explícitamente, no es un bug: dos
  usuarios de distintas compañías viendo el mismo contacto compartido
  verán colores distintos, cada uno con la paleta de su propia
  empresa.
- Si la paleta tiene un solo color, todos los avatares generados
  comparten ese color (pierden la distinción visual entre personas que
  sí daba el arcoíris de Odoo) — es el comportamiento esperado para
  "estilo uniforme de marca", documentado en el `help` del campo.

## Seguridad

- Sin modelo nuevo, sin ACL nueva: los campos viven en `res.company`,
  cuya lectura ya está abierta por el core a **cualquier usuario**
  (`base.group_public`, `base.group_portal`, `base.group_user` —
  verificado en `ir.model.access.csv`), necesario porque los avatares
  se generan en contextos muy variados (portal, anónimo, interno).
- Sin `sudo()` en ningún punto (verificado por su propio test
  `test_module_never_calls_sudo`).

## Verificación manual realizada

En navegador real: activada la paleta con el color por defecto
(`#714b67`), un contacto nuevo sin foto ("Manual Demo QA") mostró la
"M" sobre ese color exacto en su ficha — confirmado con zoom sobre el
avatar real, no solo con el test automatizado. Probado también con una
paleta de dos colores (`#1e7d3c`, `#5b6bc0`): un contacto nuevo
obtuvo `#1e7d3c` tanto en el SVG decodificado por Python
(`odoo shell`) como en la captura real del navegador — confirmando que
lo mismo que verifican los tests automatizados ocurre en el flujo real
de principio a fin. Contactos de prueba borrados y configuración
reseteada a desactivado al terminar.

## Capturas

Ver [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).
