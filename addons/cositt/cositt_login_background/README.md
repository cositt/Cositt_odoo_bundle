# Cositt Login Background

## Qué hace

Personaliza la pantalla de login de Odoo (`/web/login`) con una imagen
de fondo corporativa, color, overlay y desenfoque configurables.

## Problema que resuelve

Permite adaptar visualmente la pantalla de acceso a la identidad
corporativa de la empresa sin instalar un theme completo: subes una
imagen, activas el interruptor, y el login queda personalizado. El
resto del backend y del frontend (formularios, listas, kanban, Home
Menu, POS, website, portal) sigue exactamente igual.

## Investigación previa (arquitectura elegida)

Antes de escribir código se investigó el código fuente real de Odoo 19
(dentro del propio contenedor Docker del proyecto):

- `/web/login` lo sirve `Home.web_login()` (`web/controllers/home.py`),
  una ruta `type="http"` normal que renderiza `request.render('web.login',
  values)` — **puro QWeb del lado del servidor, sin componente OWL, sin
  SPA**. Esto simplifica mucho respecto a un patch de JavaScript: no
  hace falta esperar a que nada se monte, ni preocuparse por parpadeo,
  porque el HTML ya sale completo con el fondo aplicado.
- `web.login` vive en el módulo base `web`, dentro de `web.login_layout`
  — **ninguno de los dos depende de `web_enterprise`**. A diferencia de
  `cositt_home_wallpaper` (que sí requiere Enterprise porque el Home
  Menu de pantalla completa solo existe ahí), este módulo funciona
  igual en Community puro.
- `request` está disponible dentro de cualquier plantilla QWeb sin
  pasarlo explícitamente: `odoo/http.py` (`Request.render`) inyecta
  `self.qcontext['request'] = request` en cada render — mismo mecanismo
  que usan decenas de plantillas core. No se toca el controlador
  `Home.web_login` en ningún momento.

### Por qué el punto de anclaje final es `web.layout` y no `web.login_layout`

El primer intento heredaba `web.login_layout` directamente (parecía el
punto más específico). Se cambió tras dos hallazgos reales en
verificación manual, no supuestos:

1. **`web_enterprise` pisa `body_classname`.** `web_enterprise/views/
   webclient_templates.xml` (template `webclient_login`) también
   hereda `web.login_layout` y hace `t-set="body_classname"` de forma
   incondicional — en QWeb "el último `t-set` gana", así que una clase
   añadida a `<body>` ahí desaparecía en cuanto Enterprise está
   instalado (siempre, en este proyecto). Se comprobó en navegador: el
   fondo no aparecía y `document.body.className` mostraba
   `o_home_menu_background` sin rastro de nada propio.
2. **`website` reemplaza toda la plantilla.** El módulo `website`
   (`views/website_templates.xml`, template `login_layout`,
   `priority="20"`) hace `position="replace"` de TODO el
   `<t t-call="web.frontend_layout">` interno de `web.login_layout`. Si
   `website` llegara a instalarse, cualquier xpath apuntando dentro de
   ese `t-call` dejaría de encontrar su nodo y Odoo **reventaría al
   cargar el registro** (xpath target not found) — no solo se perdería
   el fondo, se rompería la base entera. `website` no está instalado en
   este entorno de desarrollo, pero es un módulo extremadamente común.

Por eso el diseño final ancla en `web.layout` — la plantilla más
estable de todo Odoo, la única que genera el único `<html>` de cada
respuesta (backend, portal, website y login convergen ahí,
directamente o vía cadenas de `t-call`) — y usa como filtro de alcance
la **ruta HTTP real** (`request.httprequest.path in ('/web/login',
'/web/login_successful')`) en vez de "en qué plantilla estoy". Un
`<div id="o_cositt_login_bg">` propio (nunca una clase compartida en
`<body>`) sirve de ancla para el CSS — inmune a que cualquier otro
módulo reescriba variables compartidas.

## Cómo se aplica el fondo (sin tocar plantillas core)

- Un único `<template inherit_id="web.layout">` inserta, solo cuando la
  ruta es `/web/login` o `/web/login_successful` y el fondo está
  activo: un `<style>` en `<head>` con las variables CSS ya calculadas,
  y un `<div id="o_cositt_login_bg">` en `<body>`.
- El fondo, overlay y blur se pintan con pseudo-elementos
  (`::before`/`::after`) sobre ese div, con `position: fixed` — se
  calculan contra el viewport, no contra el elemento que los genera,
  así que cubren toda la pantalla igual que si vivieran en `<body>`
  (verificado en navegador real).
- **Cero JavaScript, cero RPC.** Todo se calcula en Python
  (`_cositt_get_login_bg_config()`) y se interpola directamente en el
  HTML de la respuesta — no hay parpadeo posible porque no hay nada que
  esperar a que cargue.
- **Blur solo en el fondo, nunca en el contenido**: el `filter: blur()`
  vive únicamente en el pseudo-elemento `::before`, hermano del
  formulario de login, nunca ancestro suyo.

### Bug real corregido: `t-esc`/`t-out` rompía la URL de la imagen dentro de `<style>`

Verificación manual detectó que la imagen no cargaba aunque toda la
configuración era correcta. Causa: `<style>` es contenido "raw text" en
HTML — el navegador **no decodifica entidades ahí**. El escapado normal
de QWeb convertía las comillas de `url("...")` en `&#34;` literal
dentro del CSS, dejando `url(&#34;/web/image/...&#34;)` como texto
inválido. Corregido envolviendo los valores ya validados en
`markupsafe.Markup()` en `_cositt_get_login_bg_config()` (seguro porque
cada uno viene de una fuente controlada: el id entero de la compañía,
un color ya validado por regex, o uno de los pocos valores fijos de un
diccionario interno) y usando `t-out` sobre ellos. Test de regresión:
`test_login_page_shows_background_when_enabled` comprueba la comilla
real en la respuesta HTTP y que `&#34;` no aparece.

## Dónde vive la configuración

- **Por compañía** (`res.company`), mismo patrón que
  `cositt_home_wallpaper`: campos `cositt_login_bg_*`.
- **Imagen**: `fields.Image`, redimensionada automáticamente a un
  máximo de 2560×1440. Servida por la ruta estándar de Odoo
  (`/web/image/res.company/<id>/cositt_login_bg_image`).
- **Validación propia de formato**: solo JPG, PNG y WEBP (mismo
  hallazgo que en `cositt_home_wallpaper`: `fields.Image` no rechaza
  SVG por sí solo, así que se valida el mimetype real del contenido).
- **Hallazgo real sobre WEBP**: `odoo/tools/image.py` endurece Pillow a
  propósito (`Image.preinit()` + `Image._initialized = 2`, un
  subconjunto mínimo de formatos, sin auto-registro completo bajo
  demanda) — dentro del proceso de Odoo, Pillow no puede decodificar
  WEBP, así que `image_process()` lo detecta por sus bytes mágicos
  (RIFF/WEBPVP8) y lo guarda **sin redimensionar** (mismo trato que ya
  recibe SVG). El límite de 5 MB en bytes sigue aplicando igual; solo
  el redimensionado automático no alcanza a este formato.

## Limitación conocida (multiempresa)

`request.env.company`, para un visitante anónimo de `/web/login`,
resuelve siempre a `base.public_user.company_id` (fijado en el alta de
la base, nunca cambia solo) — **no** a una compañía elegida en el
momento del login, porque en ese punto el visitante aún no se ha
autenticado como nadie. Con una sola compañía (este entorno de
desarrollo) es invisible; en una instalación real multiempresa, todas
las visitas anónimas verían siempre el fondo de la misma compañía,
nunca el de otra, aunque cada una tenga su propia configuración
guardada. Resolverlo de verdad exigiría detección de compañía por
dominio/subdominio (terreno de `website`, fuera de alcance a
propósito). Documentado como limitación conocida del MVP, encontrada en
code review, no un bug oculto.

## Configuración

**Ajustes → Cositt - Login** (pestaña separada de la de
`cositt_home_wallpaper` a propósito: cada módulo es instalable de forma
independiente, sin depender de que el otro esté presente; si ambos
están instalados aparecen dos pestañas "Cositt" — cosmético):

1. Activa **"Fondo de login activo"**.
2. Sube una imagen (JPG, PNG o WEBP).
3. Ajusta color de respaldo, ajuste de imagen, posición, oscurecimiento
   y desenfoque a tu gusto.
4. **"Restablecer apariencia"** desactiva el fondo, borra la imagen y
   restaura los valores por defecto (pide confirmación).

## Uso

Una vez activado, el fondo aparece automáticamente en `/web/login` y en
`/web/login_successful` (la interstitial del mismo flujo de
autenticación) — el resto del backend y del frontend no cambia.

## Compatibilidad

- Odoo 19 **Community**: sí.
- Odoo 19 **Enterprise**: sí (verificado en este mismo entorno, que
  tiene Enterprise instalado — de hecho fue la verificación en
  Enterprise la que sacó a la luz el bug de `body_classname`).

## Seguridad

- Ningún modelo ni ACL nuevos: los campos viven en `res.company`, que
  ya restringe la escritura al grupo de Administración
  (`group_erp_manager`) en el propio core de Odoo. La lectura de
  `res.company` ya es abierta de fábrica (incluido `group_public`) —
  necesario para que un visitante anónimo pueda ver el fondo antes de
  autenticarse, igual que ya ocurre con el logo de la compañía en esa
  misma pantalla.
- **Sin `sudo()`** en ningún punto del módulo (verificado por su propio
  test `test_module_never_calls_sudo`).
- El color se valida contra un formato hexadecimal estricto
  (`#rrggbb`); el resto de valores interpolados en el `<style>` vienen
  de un id entero o de diccionarios internos de valores fijos — nunca
  de texto libre sin validar.

## Limitaciones

- Multiempresa: ver sección dedicada arriba.
- No hay fondos distintos por usuario ni por grupo, ni programados por
  fecha, ni carrusel, ni vídeo — fuera del alcance de este MVP a
  propósito.
- El ancho/alto máximo de la imagen guardada es 2560×1440 (excepto
  WEBP, que no se redimensiona — ver arriba); imágenes más grandes se
  redimensionan automáticamente conservando proporción.

## Capturas

Ver [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf) — capturas
reales de: login sin configurar (neutro), pantalla de configuración con
imagen subida, backend (Inventory) sin ningún rastro del fondo, y login
anónimo real con fondo, overlay y blur aplicados.

## Verificación manual realizada

Instalación limpia (login neutro por defecto, confirmado con
`curl`/HttpCase), activación con imagen JPG real, overlay 40% + blur
4px verificados visualmente en navegador como visitante anónimo real
(sesión cerrada, no solo con la cookie de admin), backend (Inventory)
confirmado sin cambios. 27/27 tests (unitarios + HTTP reales contra
`/web/login`). Dos bugs reales encontrados y corregidos durante esta
verificación (no supuestos): el pisado de `body_classname` por
`web_enterprise`, y la corrupción de `url(...)` por el escapado HTML de
`t-esc` dentro de `<style>` — ambos documentados arriba con su fix y su
test de regresión.
