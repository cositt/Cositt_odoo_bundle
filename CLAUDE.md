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

## Plugin 03 — cositt_quick_whatsapp (cerrado)

Botón de WhatsApp junto al teléfono en la ficha de Contacto. Abre
`https://wa.me/<dígitos>` en pestaña nueva. Sin modelo nuevo, sin ACL
nueva, sin dependencias externas (no usa la API de WhatsApp Business).

Alcance: solo Contactos por ahora (no CRM ni Ventas) — decisión deliberada
para no forzar instalar esas apps solo por este botón; documentado en el
README como backlog de módulos puente opcionales.

Hallazgo del review (HIGH) importante: el respaldo para cuando
`phone_sanitized` falla (sin país en la compañía, sin prefijo +CC) no
validaba nada — con un teléfono con varios números separados por "/",
o una extensión, o demasiado corto, generaba un enlace `wa.me` roto SIN
avisar al usuario. Corregido: ahora detecta esos casos y lanza `UserError`
en vez de construir un enlace inválido en silencio.

Lección reforzada (ya van 3 veces): la librería `phonenumbers` que usa
Odoo es mucho más permisiva de lo intuitivo — reconoce "00" como prefijo
internacional y limpia extensiones tipo "ext 45" *dentro del propio
`phone_sanitized`*, así que varios de mis tests iniciales fallaron por
asumir que esos casos caerían en el respaldo cuando en realidad Odoo ya
los resuelve en el camino normal. Solución: testear la función pura de
respaldo (`_extract_single_phone_digits`) de forma aislada con
`BaseCase`, sin pasar por el ORM/`phone_validation`, para no depender de
comportamiento empírico de una librería externa en los tests unitarios.

Otro hallazgo (MEDIUM) del review: el xpath para insertar el botón usaba
un índice posicional `(//field[@name='phone'])[1]` porque el campo phone
aparece dos veces en `base.view_partner_form` (cabecera + plantilla de
contactos hijos dentro del `<notebook>`) con los mismos atributos. Un
índice de documento es frágil ante reordenamientos futuros del core sin
avisar (no falla, solo coloca mal el botón). Corregido: ancla a
`div.mb8` (contenedor único de la cabecera, verificado que solo aparece
una vez en el archivo). Añadido test que verifica la posición real del
botón en el arch resuelto (antes del `<notebook>`), para que un futuro
cambio de core que rompa esto falle el test en vez de pasar desapercibido.

13 tests. Validado en navegador real: contacto con teléfono "611-222-333"
(sin prefijo, compañía con España configurada) → abrió
`api.whatsapp.com/send/?phone=34611222333...` → WhatsApp confirmó
"+34 611 22 23 33". Manual PDF generado igual que los anteriores.

## Plugin 04 — cositt_smart_attachment_name (cerrado)

Reglas simples ({campo}/{campo.subcampo}, sin código) para renombrar
adjuntos al subirlos a un modelo, vía Ajustes > Técnico. Resolución de
placeholders con `record.mapped()` (nunca eval, cero riesgo de inyección).

**Hallazgo importante de infraestructura**: esta build de Odoo 19
(20260810) **ya no soporta `_sql_constraints`** (la lista de tuplas
clásica) — se ignora en silencio con un warning en el log
("Model attribute '_sql_constraints' is no longer supported"). Hay que
usar la nueva API declarativa `models.Constraint`:
```python
_model_uniq = models.Constraint("unique(model_id)", "mensaje")
```
Aplica a cualquier plugin futuro que declare constraints SQL.

Review encontró 1 HIGH real: la restricción `unique(model_id)` bloqueaba
crear una regla nueva si la única regla anterior para ese modelo estaba
archivada (SQL unique no distingue activo/inactivo). Corregido:
`@api.constrains` en Python que solo exige unicidad entre reglas
**activas**, permitiendo archivar y reemplazar libremente. Ojo: al quitar
`models.Constraint` del código, la restricción SQL vieja quedó huérfana
en la base — Odoo la limpió solo al terminar el `-u` siguiente (no hace
falta borrarla a mano, pero sí esperar a que term "-u" complete antes de
volver a testear).

También corregidos (MEDIUM del review): valores falsy (0/False) ya no se
confunden con "campo vacío"; `{parent_id}` sin subcampo ahora usa
`display_name` en vez del repr interno del registro.

14 tests (incluye batch multi-registro, campo relacional sin subcampo,
valor 0 legítimo, reactivar regla archivada). Validado en navegador real:
regla en Contactos + subida por chatter → `Contacto_Pedro_Sánchez.pdf`
verificado directo en BD. Regla de prueba borrada después (dev limpio).

## ⚠️ Problema de entorno detectado: Enterprise/Community desincronizados

Al intentar instalar `base_iban` (que depende de `account`), Odoo
auto-instala `account_accountant` (Enterprise, `auto_install: True`) y
**revienta**: `ImportError: cannot import name '_ignore_tax_lock_date'
from odoo.addons.account.models.account_move_line`. Es un desfase de
versión entre el zip Enterprise (fechado 2026-09-10) y el Community que
trae la imagen `odoo:19.0` de Docker Hub. `account` quedó instalado (no
se pudo revertir solo desinstalando), y esto dejó una columna
`autopost_bills` en `res_partner` con NOT NULL sin default (corregido a
mano vía SQL, ver Plugin 05 abajo).

**Esto bloqueará cualquier plugin futuro que dependa de `account`**
(facturación/contabilidad). Antes de tocar esa área, hay que decidir con
el usuario: fijar una versión concreta de la imagen `odoo:19.0` que
case con este zip Enterprise, o pedir un zip Enterprise de otra fecha.
No lo he investigado más a fondo — pendiente de decisión, no de código.

## Plugin 05 — cositt_iban_validator (cerrado)

Por el problema de arriba, **no usa el `base_iban` oficial de Odoo**
(exigiría `account`). Implementación propia sobre `res.partner.bank`
(vive en `base`, no en `account`): regex de formato + tabla de longitud
por país (SEPA) + checksum ISO 7064 MOD-97-10, todo en funciones puras
sin ORM (`models/iban_validator.py`), enganchado vía
`@api.constrains("acc_number")`.

Review encontró 1 HIGH real y sutil: el regex `\d` sin `re.ASCII` acepta
dígitos Unicode no-ASCII (arábigo-índicos, etc.) que `int(ch, 36)`
normaliza en silencio — un IBAN con esos caracteres pasaba la validación
como si fuera correcto. Fix de una línea (`re.ASCII` en el regex) + test
de regresión.

Efecto colateral de este plugin: al reinstalar tras el fix, salió a la
luz el problema de `autopost_bills` (NOT NULL sin default) que había
dejado el incidente de `account_accountant` — bloqueaba crear CUALQUIER
`res.partner`. Corregido a mano con `ALTER TABLE ... SET DEFAULT 'ask'`
(valor del propio Selection de Odoo). Es un parche de entorno dev, no
parte del módulo.

13 tests. Validado en navegador real: IBAN con dígito de control
incorrecto (`ES9121000418450200051333`) rechazado con el mensaje exacto
del validador, confirmado en el log del servidor.

## Plugin 06 — cositt_email_domain_helper (cerrado)

Calcula `email_domain` (campo computado+almacenado en `res.partner`, vía
`odoo.tools.email_domain_extract` del core) y ofrece: botón en la ficha
de una persona para vincularla a la empresa existente con el mismo
dominio (excluye proveedores de email genéricos vía lista hardcodeada
`FREE_EMAIL_DOMAINS`), y menú "Dominios de email duplicados" en
Contactos con vista agrupada por dominio para detectar empresas
duplicadas. Sin modelo nuevo, sin ACL nueva (usa permisos nativos de
`res.partner`), sin dependencias externas.

Review: 0 HIGH, 2 MEDIUM, 2 LOW. Corregidos:
- Labels de UI (campo, botón, acción, menú) estaban fijos en español
  mezclados con las etiquetas en inglés del core (mismo patrón que
  plugin 02) — cambiados a inglés + `i18n/es.po` con traducción,
  exportado con `odoo i18n export` (nota de entorno: ese comando avisa
  "Ignoring not found languages: es_ES" aunque el idioma sí está activo,
  por un detalle del core que compara contra `iso_code` en vez de
  `code` — falso positivo, el .po se exporta igual).
- Faltaba `docs/manual_usuario.pdf` (el README ya enlazaba a un archivo
  inexistente).
- 1 LOW del review era falso positivo: pedía un test de "ya vinculado a
  la única empresa correcta, reintentar", pero `test_already_linked_raises`
  ya cubría exactamente ese caso — no se duplicó.
- Mensaje de error de "sin dominio" matizado para cubrir también el caso
  de email con formato no parseable (varias direcciones), no solo email
  vacío.

15 tests. Validado en navegador real con datos reales ya existentes en
la base dev: "Innova Digital SL" e "Innova Digital Sucursal Norte"
comparten dominio `innovadigital.es` — el botón detecta la ambigüedad y
no adivina; la vista agrupada muestra el grupo `innovadigital.es (2)`
correctamente. También probado el camino de vinculación única con una
empresa+contacto de prueba (creados y borrados después, sin dejar rastro
en la base dev).

Nota de entorno para sesiones futuras: `docker compose exec odoo odoo ...`
no pasa por el `entrypoint.sh` de la imagen oficial, así que no traduce
las variables `HOST`/`USER`/`PASSWORD` del compose a `--db_host` etc.
Hace falta pasarlos explícitos (`--db_host=db --db_user=... --db_password=...`)
y añadir `server --http-port=8070` (o `--no-http` si no hace falta UI)
para no chocar con el puerto 8069 del proceso principal ya corriendo.
