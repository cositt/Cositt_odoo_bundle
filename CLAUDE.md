# CLAUDE.md — contexto de sesión para este proyecto

Ver [AGENTS.md](./AGENTS.md) para arquitectura y reglas completas — este archivo solo
añade contexto específico de sesiones Claude Code.

## Estado actual

- Odoo 19.0 confirmado. Enterprise 19.0 extraído en `./enterprise/` (venía de un zip
  proporcionado por el usuario, ya descomprimido y gitignored).
- Community se obtiene vía imagen Docker oficial `odoo:19.0`, no clonada aparte.
- Puerto Odoo: `8079` (host), configurable en `.env` (`ODOO_PORT`). 8069 se evitó a
  propósito por posibles conflictos con otros proyectos Docker del usuario.
- Postgres solo accesible dentro de la red Docker (sin puerto expuesto al host).
- `.env` generado con contraseña dev aleatoria; `.env.example` sin credenciales reales.

## Plugin en curso

Fase 2/3 (entorno Docker) validada y cerrada: `cositt_hello` se creó, instaló y
eliminó correctamente para confirmar que `/mnt/cositt` funciona; la base
`cositt_plugins_dev` se recreó limpia después, sin rastro del módulo de prueba.

**Plugin 01 (`cositt_business_card_ocr`) — MVP implementado y validado.**
OCR local con Tesseract (sin enviar la imagen a ningún servicio externo),
parser heurístico de campos, detección de duplicados por email/teléfono, alta
como contacto nuevo o como persona de una empresa existente. 14/14 tests
pasando, además de una verificación manual con imagen real (Tesseract de
verdad, no mockeado) y un flujo completo en navegador (login → Contactos →
Escanear tarjeta → subir foto → extraer → crear contacto).

Hallazgo importante de esta ronda: **Odoo 19 unificó "mobile" dentro de
"phone" en `res.partner`** (ya no existe un campo `mobile` separado). Cualquier
módulo futuro que toque teléfonos de contacto debe tenerlo en cuenta.

Dockerfile ahora instala `tesseract-ocr` + `tesseract-ocr-spa` (apt) y
`pytesseract` + `Pillow` (pip) — primera dependencia añadida al proyecto,
aprobada explícitamente por el usuario.

Admin de la base de desarrollo: login `admin`, password `dev_admin_2026`
(solo válido en `cositt_plugins_dev`, entorno local, no es un secreto real).

**Code review completado y aplicado.** `code-reviewer` encontró 2 HIGH + 4
MEDIUM + 2 LOW; se corrigieron todos los HIGH/MEDIUM: manejo de errores del
OCR (excepción → `UserError` legible), detección de duplicados robusta (email
case-insensitive, teléfono normalizado por dígitos vía `phone_sanitized`),
guardas de estado contra doble confirmación, `image_filename` conectado en la
vista, `external_dependencies` en el manifest, aislamiento por usuario vía
`ir.rule` (cada uno ve solo sus escaneos; admins ven todos). 21 tests, 0 fallos.

Además, durante la verificación manual en navegador (con una segunda tarjeta
de ejemplo) apareció **otro bug real no detectado por el review ni por los
tests mockeados**: el sufijo corto "sa" en `COMPANY_SUFFIXES` hacía falso
positivo como subcadena dentro de "respon**sa**ble", clasificando mal un
cargo como nombre de empresa. Corregido comparando la última palabra completa
de la línea contra un set de sufijos, no una subcadena — moraleja: probar
con datos reales variados, no solo con el primer ejemplo que "cuadra".

**Manual PDF con capturas**: cada módulo debe incluir
`docs/manual_usuario.pdf` (ver regla nueva en AGENTS.md) generado con
capturas reales de Chrome sobre el propio entorno + Chrome headless
`--print-to-pdf`. Ya hecho para este plugin.

`git init` + primer commit ya realizados (commit `8129dbf`, rama `main`).

## Precauciones especificas de este equipo

- El usuario tiene muchas otras carpetas Odoo de clientes en su Desktop
  (`Odoo 18`, `Servidor Local Cositt`, `cashdro-prueba`, dumps `.dump`, etc.).
  Ninguna de ellas pertenece a este proyecto — no leer, copiar ni referenciar
  contenido de esas carpetas sin petición explícita.
- No hacer commit/push salvo petición explícita del usuario.
- No instalar dependencias/paquetes nuevos sin confirmar antes.
