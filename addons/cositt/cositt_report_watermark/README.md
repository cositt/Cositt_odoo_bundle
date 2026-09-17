# Cositt Report Watermark

## Qué hace

Superpone un texto de marca de agua (ej. "BORRADOR", "COPIA",
"CONFIDENCIAL") en TODOS los reportes PDF del sistema, con opacidad y
rotación configurables — sin tocar ningún reporte individual.

## Arquitectura

- Ancla en `web.report_layout`, la plantilla raíz que envuelve
  absolutamente todo reporte QWeb-PDF (investigado en el código fuente
  antes de escribir nada) — cobertura total sin depender del estilo de
  encabezado/pie que la compañía tenga elegido (standard, boxed,
  bold...).
- El texto se pinta con un único `<div>` en `position: fixed` — un
  comportamiento documentado de wkhtmltopdf (el motor de PDF de Odoo,
  confirmado instalado en este entorno): un elemento fixed dentro del
  `<body>` se repite en todas las páginas generadas, sin necesitar el
  mecanismo de header/footer que usa Odoo para report_header/footer.
- Config por compañía en `res.company` (mismo patrón que
  `cositt_home_wallpaper`/`cositt_login_background`): activo, texto,
  opacidad (0-100%), rotación (-180 a 180°).
- `env` está disponible directo en cualquier render de reporte QWeb
  (verificado: el propio core lo usa así en `report_templates.xml`) —
  no hace falta `session_info()` ni sesión HTTP, a diferencia de los
  otros dos módulos visuales.

## Hallazgo real de infraestructura (no bug del módulo)

Odoo salta el binario real de wkhtmltopdf en modo test a propósito
(`_pre_render_qweb_pdf`, condición `test_enable and not
force_report_rendering`) y devuelve HTML en su lugar, para tests
rápidos. El test de este módulo que verifica el PDF real necesita
`with_context(force_report_rendering=True)` para forzarlo.

## Configuración

**Ajustes → Cositt - Reportes**: activar, escribir el texto, ajustar
opacidad/rotación. "Restablecer" desactiva y vuelve a los valores por
defecto.

## Seguridad

Sin modelo nuevo (campos en `res.company`, mismo ACL ya existente).
Sin `sudo()` (verificado por su propio test). Valores interpolados en
el `<div>` vienen de un Char libre (texto de marca de agua, escapado
por `t-out` normal — no hay contexto `<style>` de por medio, así que
el escapado estándar es correcto aquí, a diferencia del bug real
encontrado en `cositt_login_background`) y de enteros ya validados por
rango (opacidad, rotación).

## Limitaciones

- Multiempresa: usa la compañía activa del entorno de renderizado, no
  necesariamente la del registro impreso — mismo espíritu de
  limitación documentada que `cositt_login_background`.
- No aparece en la vista previa en vivo del editor de reportes
  (`web.report_preview_layout`, una plantilla distinta) — solo en el
  PDF/HTML final generado.

## Verificación realizada

17/17 tests, incluyendo un render REAL contra el binario wkhtmltopdf
(`test_watermark_survives_real_wkhtmltopdf_render`, forzado con
`force_report_rendering=True`) sobre `base.report_irmodulereference`
(reporte del propio `base`, sin depender de `account` — bloqueado en
este entorno, ver CLAUDE.md) — confirma un `%PDF` válido generado con
el texto presente en el HTML intermedio. Confirmado también visualmente
que el texto "BORRADOR" aparece en el HTML servido real. Datos de
prueba (adjunto temporal, configuración) borrados/reseteados después.
