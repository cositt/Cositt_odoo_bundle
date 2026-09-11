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

`git init` + primer commit ya realizados. Repo remoto conectado y con push:
`github.com/cositt/Cositt_odoo_bundle` (rama `main`). Es un mono-repo para
los 12 plugins — no implica instalarlos todos juntos, cada uno sigue siendo
independiente (`__manifest__.py` propio).

## Plugin 02 — cositt_duplicate_contacts (en curso)

Decisión de arquitectura clave: **no reimplementar la fusión de contactos**.
Odoo 19 Community ya trae `base.partner.merge.automatic.wizard`
(`base.action_partner_merge` / `base.action_partner_deduplicate`), oculto sin
menú, que reasigna facturas/mensajes/actividades de forma segura al fusionar.
El plugin solo:
- Hereda ese wizard añadiendo `group_by_phone_sanitized` (reusa el campo
  `phone_sanitized` que Odoo ya normaliza, no reinventamos parsing de tel.).
- Hace un **override completo** (no `super()`) de `_generate_query`: el
  core solo excluye NULL del `GROUP BY` para email/name/vat (hardcoded, sin
  hook), así que sin este ajuste agrupar por teléfono uniría en un solo
  "grupo duplicado" a TODOS los contactos sin teléfono.
- Añade `self.env.flush_all()` porque `phone_sanitized` es un campo
  computado+almacenado y la consulta va por SQL crudo (`cr.execute`), que no
  ve valores pendientes de flush de la misma transacción — verificado
  directamente (sin el flush, `SELECT phone_sanitized ...` devolvía NULL
  aunque el recordset ya mostraba el valor calculado).
- Añade menú "Detectar duplicados" en Contactos (acción propia con
  `context` de defaults, sin tocar las acciones nativas de Odoo).

Sin dependencias externas, sin modelo nuevo, sin ACL nueva (usa los permisos
ya existentes de `base` sobre el wizard).

Validado en Docker: 5/5 tests. Validado en navegador real: creé dos
contactos "Pedro Sanchez Lopez" / "Pedro Sánchez" con el mismo teléfono en
formato distinto, el plugin los detectó y la fusión nativa transfirió el
email correctamente. Nota: hubo que fijar país España en la compañía dev
(antes en `False`) porque `phone_sanitized` no normaliza números sin
prefijo de país si la compañía no tiene país configurado — mismo hallazgo
que en Plugin 01.

**Code review completado y aplicado.** 1 HIGH + 3 MEDIUM + 3 LOW, todos
corregidos:
- Faltaba `phone_validation` en `depends` — `phone_sanitized` es de ese
  módulo (vía `contacts`→`mail` lo trae transitivo hoy, pero sin declararlo
  alguien podría desinstalarlo y romper la consulta SQL sin aviso).
- Override de `_generate_query` sin ancla de versión — añadido comentario
  explícito "re-diffear en cada upgrade de Odoo" con referencia al método
  origen.
- Defaults del menú (`Email` + `Teléfono` marcados juntos) aplicaban AND y
  ocultaban justo el caso nuevo que aporta el plugin — ahora solo
  `Teléfono` viene marcado por defecto.
- Etiqueta del campo nuevo iba fija en español mezclada con las etiquetas
  en inglés del core (Email, Name, VAT...) — cambiada a "Phone" +
  `i18n/es.po` con la traducción, verificado activando es_ES en la base
  dev (antes de esto la base dev tampoco tenía idioma español instalado,
  quedó como único activo `en_US`; ahora tiene ambos).
- Tests añadidos: combinación de criterios (AND), fusión real disparada
  por el criterio de teléfono (usando `_merge` directo, no
  `action_start_automatic_process`, que hace `cr.commit()` interno —
  comportamiento del propio core, incompatible con `TransactionCase`, con
  su propio `# TODO JEM` reconociéndolo raro).
- `@api.model` añadido al override, categoría del manifest corregida a
  "Contacts" (estaba en "Sales/CRM").

7/7 tests. Manual PDF actualizado tras el fix de defaults (capturas
regeneradas). Nota para memoria: el agente de review leyó código fuente de
Odoo (solo lectura, para comparar) desde otra carpeta del Desktop del
usuario (`cashdro-prueba/...`) no perteneciente a este proyecto — hay que
acotar explícitamente el scope de búsqueda de agentes futuros a esta
carpeta del proyecto.

## Precauciones especificas de este equipo

- El usuario tiene muchas otras carpetas Odoo de clientes en su Desktop
  (`Odoo 18`, `Servidor Local Cositt`, `cashdro-prueba`, dumps `.dump`, etc.).
  Ninguna de ellas pertenece a este proyecto — no leer, copiar ni referenciar
  contenido de esas carpetas sin petición explícita.
- No hacer commit/push salvo petición explícita del usuario.
- No instalar dependencias/paquetes nuevos sin confirmar antes.
