# Cositt Home Wallpaper

## Qué hace

Permite personalizar el fondo de la pantalla principal de aplicaciones
de Odoo (el Home Menu — el grid de iconos que aparece al entrar, antes
de elegir una app).

## Problema que resuelve

Permite adaptar visualmente Odoo a la identidad corporativa de la
empresa sin instalar un theme completo: subes una imagen, activas el
interruptor, y el Home queda personalizado. El resto del backend
(formularios, listas, kanban, chatter, configuración, POS, website,
portal, login) sigue exactamente igual.

## Investigación previa (por qué requiere Enterprise)

Antes de escribir código se investigó el código fuente de Odoo 19
(Community y Enterprise) para localizar el componente real que renderiza
el Home:

- **El Home Menu de pantalla completa (grid de apps) es un componente
  exclusivo de Enterprise**: `web_enterprise.HomeMenu`
  (`web_enterprise/static/src/webclient/home_menu/home_menu.js`),
  registrado como la acción cliente `"menu"` únicamente por
  `web_enterprise/home_menu_service.js`
  (`registry.category("actions").add("menu", HomeMenuAction)`).
- **Community no tiene un equivalente de pantalla completa.** Se
  comprobó en `web/static/src/webclient/navbar/navbar.xml`: lo que
  Community muestra para navegar entre apps es un desplegable pequeño
  anclado a la navbar (`NavBar.AppsMenu.Sidebar`), no una pantalla — la
  acción `"menu"` que dispara el Home Menu de pantalla completa no
  existe en absoluto sin `web_enterprise` instalado.
- Poner una imagen de fondo grande detrás de un desplegable de ~300px
  no cumple el objetivo del encargo ("Home Odoo → fondo
  personalizado") y se vería roto — por eso este módulo depende
  explícitamente de `web_enterprise` (`depends: ["web_enterprise"]`) en
  vez de intentar un parche parcial sobre el desplegable de Community.
  **Sin Enterprise en el `addons_path`, el módulo directamente no se
  puede instalar** (error de dependencia claro de Odoo, no un
  comportamiento oculto o degradado en silencio).

## Cómo se aplica el fondo (sin tocar plantillas core)

- `patch()` sobre `HomeMenu.prototype` (mismo mecanismo que ya usa este
  mono-repo en `cositt_list_preferences` sobre `ListRenderer`, y que usa
  el propio Odoo en `mail/chatter_patch.js`) — añade hooks
  `onMounted`/`onWillUnmount` que activan/desactivan una clase propia
  (`o_cositt_wallpaper_active`) en `<body>` **solo mientras el Home Menu
  está montado**. En cuanto se abre cualquier app, el componente se
  desmonta y la clase desaparece — por diseño, no puede quedarse "pegada"
  en otra pantalla, y nunca aparece en el login (esa pantalla nunca
  monta este componente).
- Deliberadamente **no se reutiliza** la clase nativa
  `.o_home_menu_background` de Enterprise: se comprobó en
  `web_enterprise/views/webclient_templates.xml` que esa misma clase
  también la aplica la **pantalla de login** de Enterprise. Reutilizarla
  habría arriesgado que el fondo apareciera también ahí.
- El fondo, el overlay y el blur se pintan con pseudo-elementos
  (`::before`/`::after`) sobre `body.o_cositt_wallpaper_active`, con
  `position: fixed` (igual que hace `home_menu_background.scss` del
  propio core, vía `background-attachment: fixed`) — así el fondo no se
  desplaza si el grid de apps necesita scroll en pantallas pequeñas.
  Todo el CSS vive bajo ese único selector propio; nunca se toca `body`,
  `.o_web_client` ni `.o_action_manager` de forma global ni
  incondicional.
- **Blur solo en el fondo, nunca en el contenido**: el desenfoque
  (`filter: blur()`) se aplica únicamente al pseudo-elemento `::before`
  (la capa de imagen). Los iconos y el texto del Home Menu no son
  descendientes de ese pseudo-elemento — son hermanos del elemento que
  lo genera — así que el filtro no puede alcanzarlos nunca, sea cual
  sea el valor de desenfoque configurado.

## Dónde vive la configuración

- **Por compañía** (`res.company`), no global de base: mismo patrón que
  ya usan `logo`/`logo_web` en el propio `res.company`. Al cambiar de
  compañía activa, Odoo ya fuerza una recarga completa de página
  (comprobado en `switch_company_menu.js`) — la configuración correcta
  se recalcula sola, sin código adicional para invalidar nada.
- **Imagen**: campo `fields.Image` (no `Binary` a secas) — usa
  internamente `image_process()` de Odoo, que redimensiona
  automáticamente a un máximo razonable (2560×1440 — más que suficiente
  para cualquier resolución de escritorio real, evita guardar archivos
  innecesariamente pesados). Se sirve por la ruta estándar de Odoo
  (`/web/image/res.company/<id>/cositt_wallpaper_image`), con su propia
  caché por ETag/`write_date` ya resuelta por el core.
  **Hallazgo real durante los tests (no una suposición)**: `fields.Image`
  **no rechaza SVG por sí solo** — se comprobó leyendo
  `odoo/tools/image.py`: `ImageProcess` deja pasar sin procesar
  cualquier contenido que empiece por `<` a propósito ("don't
  process... if the image is SVG"). Como un SVG puede llevar JavaScript
  embebido, este módulo valida el mimetype real del contenido
  decodificado (`_check_cositt_wallpaper_image`, solo admite
  `image/jpeg`, `image/png`, `image/webp`) — sin esta validación propia,
  un SVG se habría guardado tal cual sin ningún aviso.
- **Resto de ajustes** (activo, color, overlay, blur, ajuste, posición):
  campos normales en `res.company`.
- **Entrega al frontend sin RPC extra**: se inyecta en `session_info()`
  (`_inherit = "ir.http"`, mismo método que ya usa Odoo para
  `user_settings`/`currencies`), que llega al navegador embebido en el
  HTML inicial (`odoo.__session_info__`) — disponible antes del primer
  render del Home Menu, sin ninguna llamada de red adicional ni
  parpadeo.

## Límite de tamaño de imagen

5 MB, verificado tras el resize automático (constante
`MAX_WALLPAPER_BYTES` en `models/res_company.py`, documentada ahí
mismo). Odoo ya impone un límite global de subida para cualquier
binario (`web.max_file_upload_size`, 128 MB por defecto) — este límite
es una regla de negocio propia del módulo, más estricta, no una
sustitución de la de Odoo.

## Configuración

**Ajustes → Cositt** (pestaña nueva en Ajustes Generales, visible solo
para el grupo de Administración):

1. Activa **"Fondo personalizado activo"**.
2. Sube una imagen (JPG, PNG o WEBP).
3. Ajusta color de respaldo, ajuste de imagen (cubrir/contener/centrada/
   estirar), posición, oscurecimiento y desenfoque a tu gusto.
4. **"Restablecer apariencia"** desactiva el fondo, borra la imagen y
   restaura los valores por defecto (pide confirmación antes de borrar
   la imagen).

## Uso

Una vez activado, el fondo aparece automáticamente al entrar en Odoo
(pantalla de apps) y desaparece al abrir cualquier aplicación — el
resto del backend no cambia.

## Compatibilidad

- Odoo 19 **Enterprise**: sí (requisito — ver "Investigación previa").
- Odoo 19 **Community** puro (sin Enterprise en el `addons_path`): el
  módulo no se puede instalar (dependencia de `web_enterprise` no
  satisfecha). No es una limitación oculta: Odoo lo indica con un error
  de dependencia claro al intentar instalarlo.

## Seguridad

- Ningún modelo ni ACL nuevos: los campos viven en `res.company`, que
  ya restringe la escritura al grupo de Administración
  (`group_erp_manager`) en el propio core de Odoo — este módulo no
  amplía ni relaja ese permiso, solo se apoya en él. Un usuario normal
  puede ver el resultado (la lectura de `res.company` ya es abierta de
  fábrica) pero no puede cambiarlo.
- **Sin `sudo()` en ningún punto** del módulo (verificado por su propio
  test `test_module_never_calls_sudo`): la lectura de `res.company` para
  construir `session_info()` no lo necesita porque ya es de lectura
  abierta en el ACL base de Odoo.
- El color de fondo se valida contra un formato hexadecimal estricto
  (`#rrggbb`) antes de guardarse — nunca se interpola texto libre sin
  validar en el CSS que se genera en el navegador.

## Limitaciones

- Requiere Odoo Enterprise (ver arriba).
- No hay fondos distintos por usuario ni por grupo, ni programados por
  fecha, ni carrusel, ni vídeo — fuera del alcance de este MVP a
  propósito.
- El ancho/alto máximo de la imagen guardada es 2560×1440; imágenes más
  grandes se redimensionan automáticamente conservando proporción.

## Capturas

Ver [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf) — capturas
reales de: pantalla de configuración, Home con fondo aplicado, otra app
sin fondo, blur, diálogo de reset y Home tras restablecer.

## Verificación manual realizada (checklist del encargo)

Casos 1-4, 6-9 verificados con capturas reales en navegador; caso 5
(cover↔contain) y caso 10 (persistencia tras recargar) verificados por
código/tests + comprobación puntual. 0 errores en consola JS durante
toda la prueba. Hallazgo real durante la verificación (no una
suposición): `.o_web_client` es el propio `<body>` (no un contenedor
aparte), lo que exigió ajustar un selector CSS — documentado en
`home_menu_wallpaper.scss`.
