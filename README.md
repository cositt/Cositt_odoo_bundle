# 12 meses, 12 plugins para Odoo

Colección de módulos pequeños y gratuitos para Odoo, desarrollados por Cositt Technology,
uno por mes. Prefijo técnico: `cositt_`.

Entorno **exclusivamente de desarrollo local**. Nunca producción, nunca datos de clientes.

## Progreso: 12 / 12

| # | Módulo | Qué hace |
|---|--------|----------|
| 01 | [`cositt_business_card_ocr`](./addons/cositt/cositt_business_card_ocr) | OCR local (Tesseract) de tarjetas de visita → alta de contacto |
| 02 | [`cositt_duplicate_contacts`](./addons/cositt/cositt_duplicate_contacts) | Detección de duplicados por teléfono, sobre el wizard nativo de fusión |
| 03 | [`cositt_quick_whatsapp`](./addons/cositt/cositt_quick_whatsapp) | Botón para abrir WhatsApp (wa.me) desde la ficha de contacto |
| 04 | [`cositt_smart_attachment_name`](./addons/cositt/cositt_smart_attachment_name) | Reglas de renombrado automático de adjuntos |
| 05 | [`cositt_iban_validator`](./addons/cositt/cositt_iban_validator) | Validación de IBAN (formato + checksum) sin depender de `account` |
| 06 | [`cositt_email_domain_helper`](./addons/cositt/cositt_email_domain_helper) | Vincula contactos a su empresa por dominio de email; detecta dominios duplicados |
| 07 | [`cositt_contact_qr_vcard`](./addons/cositt/cositt_contact_qr_vcard) | QR con vCard del contacto para compartir tarjeta digital |
| 08 | [`cositt_hr_document_expiry`](./addons/cositt/cositt_hr_document_expiry) | Documentos de empleado con fecha de caducidad + recordatorio automático |
| 09 | [`cositt_stock_low_alert`](./addons/cositt/cositt_stock_low_alert) | Aviso de stock mínimo por producto, sin reglas de reabastecimiento |
| 10 | [`cositt_pdf_merge`](./addons/cositt/cositt_pdf_merge) | Combina varios PDF adjuntos a un registro en un único archivo |
| 11 | [`cositt_maintenance_qr_asset`](./addons/cositt/cositt_maintenance_qr_asset) | QR de identificación para activos de Mantenimiento |
| 12 | [`cositt_activity_digest`](./addons/cositt/cositt_activity_digest) | Menú "Mis Actividades" (todos los modelos) + posponer varias de una vez |

## Cositt Extra Modules

Ronda extra de 5 módulos genéricos adicionales, fuera de la serie mensual
de 12. Completa (13 → 17).

| # | Módulo | Descripción | Estado |
|---|--------|-------------|--------|
| 13 | [`cositt_mass_edit`](./addons/cositt/cositt_mass_edit) | Edición masiva controlada de registros | Listo |
| 14 | [`cositt_attachment_zip`](./addons/cositt/cositt_attachment_zip) | Descarga de adjuntos en ZIP | Listo |
| 15 | [`cositt_chatter_search`](./addons/cositt/cositt_chatter_search) | Añade búsqueda por autor al buscador nativo del chatter | Listo |
| 16 | [`cositt_attachment_lock`](./addons/cositt/cositt_attachment_lock) | Protección contra eliminación de adjuntos | Listo |
| 17 | [`cositt_list_preferences`](./addons/cositt/cositt_list_preferences) | Preferencias persistentes de columnas opcionales, por usuario | Listo |

## Cositt Visual Modules

Ronda de módulos que tocan la interfaz visual del backend/frontend
(QWeb/OWL/SCSS), fuera de las dos series anteriores.

| # | Módulo | Descripción | Requiere | Estado |
|---|--------|-------------|----------|--------|
| 1 | [`cositt_home_wallpaper`](./addons/cositt/cositt_home_wallpaper) | Fondo personalizado del Home Menu (imagen, color, overlay, blur) | Enterprise | Listo |
| 2 | [`cositt_login_background`](./addons/cositt/cositt_login_background) | Fondo personalizado de la pantalla de login (imagen, color, overlay, blur) | Community + Enterprise | Listo |
| 3 | [`cositt_kanban_ribbon_theme`](./addons/cositt/cositt_kanban_ribbon_theme) | Ribbon de color en tarjetas kanban de los modelos que elijas (reusa la paleta nativa) | Community + Enterprise | Listo |
| 4 | [`cositt_report_watermark`](./addons/cositt/cositt_report_watermark) | Marca de agua de texto configurable en todos los reportes PDF | Community + Enterprise | Listo |
| 5 | [`cositt_backend_accent`](./addons/cositt/cositt_backend_accent) | Color de acento configurable para botones primarios, checkboxes/radios e ítem de menú activo del backend | Community + Enterprise | Listo |
| 6 | [`cositt_company_favicon`](./addons/cositt/cositt_company_favicon) | Favicon (PNG) y título de pestaña personalizados por compañía, en todo el sitio | Community + Enterprise | Listo |
| 7 | [`cositt_announcement_banner`](./addons/cositt/cositt_announcement_banner) | Banner superior configurable (mensaje + estilo) para avisos internos del backend | Community + Enterprise | Listo |
| 8 | [`cositt_seasonal_theme`](./addons/cositt/cositt_seasonal_theme) | Icono temático + partículas animadas opcionales (Navidad/Feria/Cumpleaños/Campaña), con rango de fechas | Community + Enterprise | Listo |

`cositt_home_wallpaper` requiere **Odoo Enterprise** (el Home Menu de
pantalla completa no existe en Community — ver el README del propio
módulo para el porqué, investigado en el código fuente antes de
construirlo). `cositt_login_background` funciona en Community puro (la
pantalla de login vive en el módulo base `web`, no en `web_enterprise`).

### Backlog (pendiente)

| # | Módulo | Idea | Notas |
|---|--------|------|-------|
| 5 | ~~`cositt_login_branding`~~ | Logo, mensaje y colores de empresa en el login | **Hecho** — extendido `cositt_login_background` en vez de crear módulo nuevo (mensaje + color de acento; el logo ya lo muestra el core sin cambios). Ver README de ese módulo. |
| 6 | ~~`cositt_backend_accent`~~ | Elegir color corporativo para botones y elementos activos del backend | **Hecho** — módulo nuevo, tabla de arriba (#5 de Visual Modules). |
| 7 | ~~`cositt_company_favicon`~~ | Favicon y título del navegador personalizados por empresa/base | **Hecho** — módulo nuevo, tabla de arriba (#6 de Visual Modules). |
| 8 | ~~`cositt_announcement_banner`~~ | Banner superior configurable para avisos internos | **Hecho** — módulo nuevo, tabla de arriba (#7 de Visual Modules). |
| 9 | ~~`cositt_seasonal_theme`~~ | Decoraciones ligeras programables (Navidad, feria, aniversario, campaña...) | **Hecho** — módulo nuevo, tabla de arriba (#8 de Visual Modules). |
| 10 | ~~`cositt_kanban_style`~~ | Más opciones visuales para tarjetas kanban: bordes, indicadores | **Hecho** — extendido `cositt_kanban_ribbon_theme` en vez de crear módulo nuevo (campo `style`: ribbon/borde/punto). Ver README de ese módulo. |
| 11 | `cositt_user_avatar_style` | Avatares automáticos con iniciales, colores y estilo uniforme | — |

Sin orden de prioridad fijo. Antes de empezar cualquiera, revisar si el
core de Odoo ya lo resuelve (mismo criterio que evitó duplicar trabajo
en el plugin 09 — ver CLAUDE.md).

Cada módulo es independiente (`__manifest__.py` propio) e instalable por
separado — el mono-repo no implica instalarlos todos juntos. Detalle de
cada uno, decisiones de arquitectura y hallazgos de cada ronda de review
en [CLAUDE.md](./CLAUDE.md).

## Stack

- Odoo **19.0** (Community vía imagen oficial `odoo:19.0` + Enterprise montado como volumen)
- PostgreSQL 16
- Docker Compose

## Estructura

```
.
├── docker-compose.yml
├── Dockerfile              # FROM odoo:19.0 (punto de extensión para deps futuras, ej. OCR)
├── config/odoo.conf
├── enterprise/              # Odoo Enterprise 19.0 (NO se sube a git, licenciado)
├── addons/cositt/           # Módulos propios Cositt (cositt_xxx)
├── scripts/
├── docs/
├── tests/
├── .env                     # credenciales dev, NO se sube a git
└── .env.example
```

## Levantar el entorno

```bash
cp .env.example .env   # si no existe ya
docker compose up -d
docker compose ps
docker compose logs -f odoo
```

Odoo queda accesible en [http://localhost:8079](http://localhost:8079) (puerto configurable
en `.env` vía `ODOO_PORT`).

## Crear base de desarrollo

Desde el asistente de creación de base de datos de Odoo (primera pantalla al entrar), o:

```bash
docker compose exec odoo odoo -d cositt_plugins_dev --db_host=db -i base --stop-after-init
```

Nombre sugerido: `cositt_plugins_dev`. Nunca usar dumps ni bases de clientes reales.

## Activar modo desarrollador

Ajustes → Activar el modo desarrollador (o añadir `?debug=1` a la URL).

## Actualizar un módulo Cositt

```bash
docker compose exec odoo odoo -d cositt_plugins_dev -u cositt_nombre_modulo --stop-after-init
docker compose restart odoo
```

Los módulos en `addons/cositt/` están montados como volumen: los cambios de código se
reflejan sin reconstruir la imagen (solo hace falta reiniciar/actualizar el módulo).

## Tests

```bash
docker compose exec odoo odoo -d cositt_plugins_dev --test-enable -i cositt_nombre_modulo --stop-after-init
```

## Buenas prácticas

- Un módulo, una función concreta.
- Community + Enterprise cuando sea posible; documentar si algo requiere Enterprise.
- No modificar core de Odoo ni los fuentes de Enterprise.
- No SQL directo salvo necesidad real; usar el ORM.
- Cada módulo con su propio README (ver plantilla en `docs/`).

Ver también [AGENTS.md](./AGENTS.md) y [CLAUDE.md](./CLAUDE.md) para contexto de agentes IA.
