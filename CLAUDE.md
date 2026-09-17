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

## Plugin 07 — cositt_contact_qr_vcard (cerrado)

Pestaña "Digital Card" en la ficha de contacto con un código QR generado
localmente (nombre, empresa, cargo, teléfono, email, dirección, web en
formato vCard 3.0). Campo `qr_vcard` (Binary, computado, `store=False`)
en `res.partner`, sin modelo nuevo, sin ACL nueva.

**Hallazgo de entorno importante**: la librería Python `qrcode` ya viene
incluida en la imagen oficial `odoo:19.0` (la usa el propio core para el
QR de `auth_totp` y otros módulos) — no hizo falta tocar el Dockerfile ni
pedir confirmación de dependencia nueva. Verificado con
`docker compose exec odoo python3 -c "import qrcode"` antes de empezar.
Aplica a cualquier plugin futuro que necesite generar QR.

Sobre cómo generar el `i18n/es.po` desde el CLI en Odoo 19: el comando ya
no es `--i18n-export` (ese flag ya no existe), es el subcomando
`odoo i18n export -d <db> <modulo> -l es_ES`. Ese subcomando tampoco lee
`--db_host`/`--db_user`/`--db_password` ni la config montada en
`/etc/odoo/odoo.conf` (que no trae credenciales de base de datos, solo
`addons_path` — las credenciales las inyecta el `entrypoint.sh` oficial
vía variables `PG*`, que `docker compose exec` no ejecuta). Hace falta
pasar `-e PGHOST=db -e PGUSER=... -e PGPASSWORD=...` al propio
`docker compose exec` para que psycopg2 los recoja.

**Code review**: 2 HIGH + 3 MEDIUM + 3 LOW, HIGH y MEDIUM corregidos:
- El `try/except` que protegía la generación del QR envolvía solo
  `_generate_qr_png`, no la construcción de la vCard (que lee
  `country_id.name`, antes `parent_id.name`) — un `AccessError` ahí
  habría roto la carga del formulario de contacto para todo el sistema,
  justo lo que el propio comentario del código decía evitar. Ahora el
  `try/except` envuelve ambos pasos dentro de `_compute_qr_vcard`.
- El escapado RFC 6350 solo cubría `\n`, no un `\r` suelto (sin pareja
  `\n`) ni `\r\n` — quedaba como carácter de control real en la vCard, y
  varios lectores lo tratan igual que un salto de línea, lo que
  permitiría inyectar una propiedad falsa (otro TEL/EMAIL) a través de un
  campo de texto libre como el nombre. Corregido normalizando cualquier
  variante de salto de línea a `\n` antes de escapar.
- La dirección (ADR) exigía `street` para incluirse, perdiendo
  ciudad/país si solo faltaba la calle — ahora se incluye si hay
  cualquier componente de dirección. Se aprovechó para añadir `street2`
  como "extended address" del vCard.
- El ORG de una persona solo miraba `parent_id.name` (empresa vinculada
  por registro), ignorando el caso de "Company Name" como texto libre sin
  empresa vinculada — cambiado a `commercial_company_name` (campo nativo
  de Odoo que cubre ambos casos), y la dependencia del campo computado
  actualizada de `parent_id.name` a `commercial_company_name`.
- Añadido comentario de advertencia junto al campo: no-stored, pensado
  para el formulario (un registro), no para listas/kanban/export masivo.

29 tests (arrancó en 23, +6 tras los fixes del review). Validado en
navegador real: QR visible y legible en la ficha de "Pedro Sánchez" y de
"Maria Lopez Fernandez" (con empresa, cargo, teléfono y web reales de la
base dev). Probado también el caso límite de la vCard con un contacto
nuevo sin guardar cuyo nombre incluía coma, punto y coma y backslash a la
vez (`Perez, Juan; Test\Backslash`) — sin traceback, escapado correcto en
integración real, no solo en el test unitario. Registro de prueba
descartado sin guardar, base dev sin rastro. Manual PDF generado con
capturas reales de este mismo flujo.

Pendiente de commit (no se hace commit salvo petición explícita) —
Plugin 06 (`cositt_email_domain_helper`) tampoco estaba comiteado al
empezar esta sesión, sigue así.

Backlog de ideas discutidas para próximos meses (no comprometidas a
orden fijo): `cositt_project_task_aging` (badge de tareas estancadas en
Proyecto), `cositt_stock_low_alert` (aviso de stock mínimo en
Inventario), `cositt_maintenance_qr_asset` (QR de activo en
Mantenimiento, mismo hallazgo de `qrcode` ya disponible que plugin 07).

## Plugin 08 — cositt_hr_document_expiry (cerrado)

Documentos de empleado con fecha de caducidad (DNI, permiso de trabajo,
carné...) en nuevo modelo `hr.employee.document` (One2many desde
`hr.employee`). Un cron diario crea una actividad "Por hacer" (reutiliza
`mail.mail_activity_data_todo` del core, sin tipo de actividad nuevo)
antes de que caduque, asignada al empleado o a su responsable directo si
no tiene usuario; si ninguno tiene usuario, se registra un warning en el
log y se salta ese documento sin romper el cron para los demás.

**Hallazgo de entorno importante**: `hr` no estaba instalado en la base
dev (nunca se había tocado la app Empleados en este proyecto) — al
instalarlo arrastra `hr_skills` y `mail_bot_hr` como `auto_install`,
ninguno depende de `account`, sin problema.

**Otro hallazgo de entorno, más raro**: tras crear el directorio del
módulo nuevo y hacer `-i` vía `docker compose exec` (proceso corto), el
proceso PRINCIPAL de Odoo (el que sirve el puerto 8069, arrancado por
`entrypoint.sh` al levantar el contenedor) falló con
`ModuleNotFoundError: No module named 'odoo.addons.cositt_hr_document_expiry'`
al intentar servir una petición — un `ls` desde otro `docker compose exec`
mostraba los archivos perfectamente. No pasó con los plugins 06/07
creados en la misma sesión. Causa más probable: caché de listado de
directorio del propio proceso largo-vivo sobre el volumen bind-mounted
(Docker Desktop/macOS), no relacionado con el código del módulo. Fix:
`docker compose restart odoo`. Si un módulo nuevo da este error exacto en
sesiones futuras, probar el restart antes de sospechar del código.

**Code review**: 1 HIGH + 3 MEDIUM + 1 LOW. Corregidos:
- HIGH: `hr.employee.document` no tenía `company_id` ni `ir.rule`, a
  diferencia de `hr.employee` (que sí tiene una regla multi-compañía
  nativa) — cualquier usuario con `hr.group_hr_user` podía leer/escribir
  documentos (DNI, permiso de trabajo: PII sensible) de empleados de
  OTRA compañía vía acceso técnico/API, aunque la navegación normal por
  la ficha de empleado ya estuviera protegida. Añadido `company_id`
  (related a `employee_id.company_id`, stored) + `ir.rule` multi-compañía
  estándar en `security/hr_employee_document_security.xml`.
- MEDIUM: el cálculo `expiry_date - reminder_days_before` estaba
  duplicado en la función pura de estado y en el compute de
  `alert_date` — mismo riesgo de divergencia futura que se vigila en
  otros plugins. Extraído a un único helper `_compute_alert_date_value`.
- MEDIUM: el cron no aislaba fallos por documento — un error creando la
  actividad de uno habría revertido (por el commit único de `ir.cron` al
  final) las ya creadas para los anteriores en la misma pasada. Cada
  `activity_schedule` ahora va dentro de `self.env.cr.savepoint()`.
- MEDIUM (documentado, no cambia código): la idempotencia del cron solo
  mira actividades ABIERTAS — si alguien marca el recordatorio como
  hecho sin renovar `expiry_date`, el cron del día siguiente crea uno
  nuevo. Es el comportamiento deseado (seguir avisando hasta que se
  renueve), ahora explícito en un comentario en el código.
- LOW: el xpath de la vista anclaba a `//notebook` genérico — cambiado a
  `//page[@name='hr_settings']` (última página nativa), igual que hacen
  `hr_org_chart`/`hr_skills` al añadir páginas ahí.

22 tests (arrancó en 20, +2 tras los fixes: `company_id` sigue al
empleado, y un usuario de una compañía no ve documentos de otra).
Validado en navegador real: empleada de prueba con documento "DNI" y
fecha dentro de la ventana de aviso → badge "Expiring soon" correcto;
cron ejecutado a mano dos veces sobre datos reales (una sin usuario
vinculado, confirmando el warning + no-crash; el camino con usuario ya
cubierto por los tests de integración). Registro de prueba borrado
después, base dev limpia.

## Plugin 09 — cositt_stock_low_alert (cerrado)

Umbral de stock mínimo por producto (`low_stock_threshold` en
`product.template`) + `is_low_stock` computado. Cron diario crea un
aviso cuando el stock cae al umbral o por debajo, asignado al
`responsible_id` **nativo** de `stock` (reutilizado a propósito, no se
añadió campo de responsable propio). Complementa, no sustituye, a las
Reordering Rules nativas (`stock.warehouse.orderpoint`), que exigen
ruta de compra/fabricación configurada — este plugin es solo un aviso.

**Descarte de plugin evitado**: la idea original del mes ("aging" de
tareas estancadas en Proyecto) resultó ser una función YA NATIVA de
Odoo 19 (`mail.tracking.duration.mixin`, campos `is_rotting`/
`rotting_days`, widget `rotting` ya cableado en el kanban de
`project.task`) — simplemente apagada por defecto
(`rotting_threshold_days = 0` en todas las etapas). Se descartó ese
plugin por sería puro duplicado, y se pasó a "alerta de stock mínimo"
del backlog. Lección: investigar SIEMPRE si el core ya resuelve la idea
antes de escribir código — casi se repite el trabajo de Odoo.

**Bug de vista real encontrado y corregido durante el desarrollo**: un
`<group>` HERMANO nuevo añadido al final de `<page name="inventory">`
nunca se pintaba en el navegador, aunque el servidor devolvía el campo
correctamente en el arch (verificado con RPC directo) — la página tiene
un layout de 2 columnas con 2 `<group>` esperados. Un segundo intento
con xpath posicional (`group[1]`) funcionó por casualidad pero es
frágil. Fix final: anclar a `group[@name='group_lots_and_weight']`
(nombre fijo, siempre presente para productos Goods), igual que hace el
propio `stock` en tres xpaths distintos sobre esa vista.

**Code review**: 2 HIGH + 1 MEDIUM + 3 LOW. Corregidos:
- HIGH: el chequeo "ya avisado" del cron miraba CUALQUIER actividad
  To-Do abierta en el producto, no una creada por este plugin —
  `product.template` es un modelo de uso muy común donde cualquiera
  puede tener ya un To-Do por un motivo ajeno (ej. "llamar al
  proveedor"), lo que silenciaba el aviso real de stock bajo para
  siempre, sin loguear nada. Fix: tipo de actividad propio
  ("Low Stock Alert", `data/mail_activity_type.xml`, con
  `res_model='product.template'`) en vez de reutilizar el "To-Do"
  genérico del core.
- HIGH: `responsible_id` es `company_dependent` y el cron corre con el
  contexto de una sola compañía (la del usuario del `ir.cron`) — un
  producto compartido entre compañías (`company_id=False`) podía
  resolver el responsable de la compañía equivocada. Fix: forzar
  `product.with_company(product.company_id or self.env.company)`
  explícitamente antes de leer `responsible_id`; si el producto no
  tiene `company_id` propio, se registra un warning explícito en vez de
  fallar en silencio (caso límite documentado, no resuelto del todo —
  ver README).
- MEDIUM: el `help` de `low_stock_threshold` no avisaba de que en
  productos con variantes el umbral compara contra el stock combinado
  de todas ellas, no de una variante concreta — añadido al help text.
- LOW: limpieza de condición redundante en `_is_low_stock`, quitado
  `widget="boolean_toggle"` de un campo readonly (sugería
  interactividad que no tiene), formato de cantidad en el summary del
  aviso (`%(qty)s` con `:g` para no mostrar "3.0").

17 tests (arrancó en 15, +2 tras los fixes: un To-Do ajeno no bloquea
el aviso real, y un producto con `company_id` propio resuelve bien el
responsable). Validado en navegador real: producto de prueba con
umbral 10 y stock 0 → "Is Low Stock" se activa al momento (onchange en
vivo); cron ejecutado a mano sobre datos reales → actividad "Low stock:
Producto Test Stock (0.0 available, threshold 10.0)" creada y asignada
correctamente. Registro de prueba borrado después.

## Cositt Visual Modules 02 — cositt_login_background (cerrado)

Fondo personalizado de la pantalla de login (`/web/login`), hermano de
`cositt_home_wallpaper` pero con arquitectura muy distinta: renderizado
100% servidor (QWeb puro, cero JS/RPC), y funciona en **Community +
Enterprise** (la pantalla de login vive en el módulo base `web`, no en
`web_enterprise`).

**Dos bugs reales encontrados y corregidos en verificación manual en
navegador** (ninguno detectado antes de probar de verdad, ninguno lo
habría atrapado un test que solo mirara `_cositt_get_login_bg_config()`
de forma aislada):

1. **`web_enterprise` pisaba el fondo.** El diseño inicial heredaba
   `web.login_layout` y añadía la clase propia vía `t-set="body_classname"`
   aditivo. `web_enterprise/views/webclient_templates.xml` (template
   `webclient_login`) también hereda `web.login_layout` y hace
   `t-set="body_classname"` incondicional — "el último `t-set` gana" en
   QWeb, así que la clase desaparecía en cuanto Enterprise está
   instalado (siempre, en este proyecto). Confirmado en navegador:
   `document.body.className` mostraba `o_home_menu_background` sin
   rastro de nada propio, aunque la config estaba bien guardada en BD.
   Peor aún, investigando el porqué: el módulo `website` (no instalado
   aquí, pero muy común) hace `position="replace"` de TODO el
   `<t t-call="web.frontend_layout">` interno de `web.login_layout` —
   si se instalara, cualquier xpath apuntando ahí dentro habría hecho
   **reventar la carga del registro entero** (xpath target not found),
   no solo perder el fondo.
   Fix: rediseño completo del punto de anclaje a `web.layout` (la
   plantilla raíz, la única que genera el único `<html>` de cada
   respuesta — nunca reemplazada por nadie), con el alcance decidido
   por `request.httprequest.path` en vez de "en qué plantilla estoy", y
   un `<div id="o_cositt_login_bg">` propio en vez de una clase
   compartida en `<body>`.
2. **`t-esc`/`t-out` corrompía la URL de la imagen.** `<style>` es
   contenido "raw text" en HTML — el navegador no decodifica entidades
   ahí. El escapado normal de QWeb convertía las comillas de
   `url("...")` en `&#34;` literal DENTRO del CSS, dejando
   `url(&#34;/web/image/...&#34;)` como texto inválido — la imagen
   nunca cargaba aunque toda la configuración fuera correcta. Fix:
   envolver los valores ya validados en `markupsafe.Markup()` dentro de
   `_cositt_get_login_bg_config()` (seguro: vienen de un id entero, un
   color ya validado por regex, o valores fijos de un diccionario
   interno — nunca texto libre) y usar `t-out` sobre ellos.

Mismo hallazgo que en `cositt_home_wallpaper` sobre WEBP y SVG con
`fields.Image`, más uno nuevo: `odoo/tools/image.py` endurece Pillow a
propósito (`Image.preinit()` + `Image._initialized = 2`) — dentro del
proceso de Odoo, Pillow no puede codificar/decodificar WEBP, así que
`image_process()` lo detecta por bytes mágicos (RIFF/WEBPVP8) y lo
guarda sin redimensionar (mismo trato que SVG). Esto también rompió el
primer intento de test con WEBP generado con PIL dentro del propio
proceso de test de Odoo (`KeyError: 'WEBP'`) — solucionado con un WEBP
real de 40×30 generado UNA VEZ fuera de Odoo y embebido como bytes
fijos en el test.

Code review (agente, antes del rediseño de arquitectura) encontró 1
HIGH real y aceptado como limitación documentada (no arreglado, fuera
de alcance a propósito): `request.env.company` para un visitante
anónimo de `/web/login` resuelve siempre a `base.public_user.company_id`
(fijado al alta de la base, nunca cambia solo), no a una compañía
elegida en el momento del login — en multiempresa real, todas las
visitas anónimas verían siempre el fondo de la MISMA compañía.
Documentado en el docstring de `_cositt_get_login_bg_config()` y en el
README. Los MEDIUM del mismo review (falta de README/manual, falta de
test de imagen servida a anónimo real, falta de test de que el fondo no
se cuele en el backend) sí se corrigieron.

27 tests (unitarios + `HttpCase` reales contra `/web/login`,
`/web/login_successful` y `/odoo` autenticado — no solo
`TransactionCase` aislado). Nota de proceso: hacer verificación manual
en navegador ANTES de la tanda final de tests automatizados dejó
estado (`cositt_login_bg_enabled=True` en la compañía) que rompió 2-3
tests que asumían valores por defecto — hubo que resetear la compañía a
mano (`UPDATE res_company ...` + borrar el `ir.attachment` de la
imagen, que no es una columna de la tabla al ser `fields.Image` sin
`attachment=False`) antes de la corrida limpia final. Para sesiones
futuras: correr los tests automatizados ANTES de cualquier exploración
manual en el mismo entorno compartido, no después.

Validado en navegador real como visitante anónimo genuino (sesión de
admin cerrada explícitamente, no solo pestaña nueva con cookie viva):
login neutro por defecto, imagen real subida con overlay 40%/blur 4px
aplicados correctamente y formulario legible, Inventario (backend) sin
ningún rastro del módulo. Manual PDF generado con capturas de este
mismo flujo.

## Cositt Visual Modules 03 — cositt_kanban_ribbon_theme (cerrado)

Ribbon de color en tarjetas kanban de los modelos que el admin elija,
reusando un campo Integer existente (típicamente `color`, el mismo del
selector de color nativo de Odoo). Config: modelo
`cositt.kanban.ribbon.rule` (Ajustes → Técnico, mismo patrón que
`cositt_smart_attachment_name`: `model_id` + nombre de campo + `active`,
unicidad solo entre activas). Entrega al frontend vía `session_info()`
(mismo patrón zero-RPC que wallpaper/login_background); aplicación vía
`patch()` de `KanbanRecord.getRecordClasses()` — no una plantilla OWL
heredada. CSS reusa `$o-colors` (paleta nativa de 12 colores, la misma
del selector "Establecer color"), cero colores propios inventados.

**Bug real HIGH encontrado en code review y corregido**: el diseño
inicial leía `rule.model_id.model` directamente dentro del método que
`session_info()` llama para CUALQUIER usuario en cada carga del
backend. `model_id.model` es un campo de `ir.model` (otro modelo) —
leerlo dispara una comprobación de ACL real, y el ACL base de Odoo da
CERO acceso a `ir.model` para `base.group_user` (usuarios internos
normales). Con una sola regla activa, `/odoo` reventaba con
`AccessError` para todo usuario no-administrador — tumbaba el backend
entero para ellos, no solo el kanban. Reproducido de verdad contra este
mismo `cositt_plugins_dev` antes del fix. Corregido con un campo
denormalizado `model_name` (`related="model_id.model", store=True`) en
la propia regla: se calcula una vez cuando escribe un admin (que sí
tiene acceso a `ir.model`), y `session_info()` lee ese Char normal, ya
cubierto por el ACL de lectura abierto a `group_user` — sin `sudo()`.
Mismo espíritu que ya seguían wallpaper/login_background (construir
`session_info()` sobre algo ya legible por todos), pero esta vez el
"algo" era un modelo restringido y hubo que denormalizar para lograrlo.

Otros hallazgos del mismo review, corregidos:
- Índice de color negativo: `getColorIndex()` del core usa `%` nativo
  de JS (conserva el signo) — un campo Integer legítimamente negativo
  daría una clase CSS que no coincide con nada (`o_colorlist_item_color_-3`),
  ribbon invisible en vez de mostrar color. Normalizado a módulo
  verdadero en el JS.
- Aislamiento de tests: varios asumían base de datos limpia
  (`search([])` sin filtrar) — en este entorno de dev compartido con
  verificación manual, eso rompía tests con datos de sesiones
  anteriores (5/14 fallaban así en la corrida del reviewer). Reescritos
  para trabajar sobre el recordset propio de cada registro creado.
- Comentario impreciso sobre modo oscuro (decía que `$o-colors` se
  redefine ahí; no es así — corregido para explicar la razón real de
  la consistencia: el propio indicador nativo tampoco lo ajusta).
- `position: relative` redundante en el SCSS (ya lo trae
  `.o_kanban_record` del core) — eliminado.
- Documentadas como limitación (no resueltas, fuera de alcance): una
  regla sobre un campo que la vista kanban de destino no carga no
  muestra error, simplemente no aparece; una regla sobre un campo que
  luego se elimina del modelo queda inactiva en la práctica sin aviso.

16 tests (incluye regresión HTTP real del bug HIGH: usuario interno
nuevo, no admin, con una regla activa, `/odoo` responde 200 en vez de
500). Validado en navegador real: regla creada para `project.task`,
tarea de prueba con color asignado vía el selector nativo → ribbon
visible con el color correcto; kanban de Inventario (sin regla) sin
ningún cambio. Datos de prueba borrados después, base dev limpia.

## Cositt Visual Modules 04 — cositt_report_watermark (cerrado)

Marca de agua de texto configurable (texto/opacidad/rotación, por
compañía en `res.company`) en TODOS los reportes PDF. Ancla en
`web.report_layout` (la plantilla raíz de cualquier reporte QWeb-PDF,
investigado antes de escribir código) — cobertura total sin tocar
reportes individuales ni variantes de encabezado/pie (standard/boxed/
bold...). Pintado con un único `<div position:fixed>`: comportamiento
documentado de wkhtmltopdf donde un fixed dentro de `<body>` se repite
en todas las páginas, sin necesitar el mecanismo de header/footer que
usa Odoo para `report_header`/`report_footer`. Arquitectura más simple
que los otros dos módulos visuales: `env` está disponible directo en
cualquier render de reporte QWeb (verificado en el propio core), sin
`session_info()` ni sesión HTTP de por medio — así que la clase de bug
ACL que apareció en `cositt_kanban_ribbon_theme` no aplica aquí.

Hallazgo real de infraestructura (no bug): Odoo salta wkhtmltopdf en
modo test a propósito (`_pre_render_qweb_pdf`, `test_enable and not
force_report_rendering`) y devuelve HTML en su lugar — el test que
verifica el PDF real necesitó `with_context(force_report_rendering=True)`
para forzar el binario de verdad. Reporte usado para probar: el propio
`base.report_irmodulereference` (sin depender de `account`, bloqueado
en este entorno).

17/17 tests, incluye un render real contra wkhtmltopdf (PDF válido
`%PDF` generado con el texto presente). Confirmado visualmente que el
texto de marca de agua aparece en el HTML/PDF servido real. Sesión
cerrada con presupuesto de contexto ajustado — verificación visual del
PDF final (rotación/centrado exactos) quedó apoyada en el HTML
intermedio + generación real del binario, no en una captura del PDF ya
renderizado en el visor de Chrome (que no cargaba de forma fiable en
las capturas); recomendable que el usuario haga una revisión visual
rápida del PDF real la próxima vez que lo use.

## Estado de la ronda "Cositt Visual Modules": 4/4 completos

`cositt_home_wallpaper`, `cositt_login_background`,
`cositt_kanban_ribbon_theme`, `cositt_report_watermark` — los 3 últimos
completados en una misma sesión larga, cada uno con al menos un bug
real encontrado en verificación manual o code review (nunca solo en
tests aislados) y corregido antes de cerrar. Comiteado y pusheado
(`b9ff7b9`).

## Backlog "Visual Modules 5-11" — #5 y #10 cerrados (extendiendo módulos existentes)

Ronda posterior: el usuario pidió atacar primero las dos ideas del
backlog marcadas como solapadas con módulos ya existentes (#5
`cositt_login_branding`, #10 `cositt_kanban_style`), para "quitárselas
de encima". Decisión de arquitectura en ambos casos: **extender el
módulo existente, no crear uno nuevo** — evita duplicar el mecanismo
de configuración/seguridad ya revisado, consistente con la nota que ya
dejaba el propio backlog del README raíz.

**#5 → `cositt_login_background`** ganó dos campos nuevos en
`res.company`: `cositt_login_bg_message` (Char, máx. 140, escapado con
`t-esc`, nunca `Markup()` — es texto libre de un admin) y
`cositt_login_bg_accent_color` (Char hex, mismo regex que el color de
fondo, inyectado como variable CSS `--cositt-login-accent` en `:root`
porque el botón/enlaces del login viven fuera del div
`#o_cositt_login_bg` en el DOM). El mensaje se ancla en
`oe_structure_login_top`, el punto de extensión nativo que `web.login`
ya declara para esto — no hizo falta tocar `web.layout` ni el filtro
por `request.httprequest.path` que sí necesita el fondo. El logo NO
necesitó campo nuevo: `web.login_layout` ya muestra
`company_logo` nativo. Ambos campos nuevos comparten el mismo
interruptor que el fondo (`cositt_login_bg_enabled`), reetiquetado de
"Fondo de login activo" a "Personalización de login activa" (hallazgo
MEDIUM de code review: el nombre viejo era engañoso una vez el campo
pasó a gobernar tres cosas, no solo el fondo — se corrigió el label sin
tocar el nombre técnico del campo, para no forzar una migración).
37/37 tests.

**#10 → `cositt_kanban_ribbon_theme`** ganó un campo `style` (Selection:
`ribbon`/`border`/`dot`, default `ribbon`) en `cositt.kanban.ribbon.rule`.
`_cositt_get_active_ribbon_rules()` cambió de forma
(`{modelo: campo_color}` → `{modelo: {"field":..., "style":...}}`) —
sin romper nada externo (grep del repo entero confirmó que ningún otro
módulo depende de la forma vieja). **Bug real encontrado en
verificación manual, ni en tests ni en code review**: el estilo "dot"
se diseñó primero en la esquina superior derecha, igual que el ribbon
— en navegador real, al pasar el ratón, el menú contextual nativo "⋮"
de kanban aparece exactamente ahí y tapa el punto. Ningún test lo
detecta (ninguno simula `:hover` ni renderiza CSS real). Corregido
moviendo el punto a la esquina superior izquierda. 18/18 tests.

Ambos con code review (1 agente cada uno, en paralelo): 0
CRITICAL/HIGH en los dos. MEDIUM corregidos: el toggle mal nombrado de
arriba, y en ambos módulos el README no se había actualizado tras el
cambio (corregido) y el manual PDF no se había regenerado (regenerado
con capturas reales nuevas: panel de Ajustes con mensaje/acento,
`/web/login` anónimo real con el mensaje y el botón en el color de
acento, formulario de regla con el campo "Estilo", tarjetas kanban con
border y con dot). Tabla de backlog del README raíz actualizada
marcando #5 y #10 como hechos.

**Lección de proceso repetida** (ya iba una vez en la ronda anterior de
este mismo módulo, ver README de `cositt_login_background`): dejar
`cositt_login_bg_enabled=True` en la compañía real tras la
verificación manual en navegador rompió 2 tests al re-correr la suite
después. Sección `[[feedback-odoo-plugin-workflow]]` de memoria
actualizada con esto — rerun de tests SIEMPRE después de cualquier
exploración manual en `cositt_plugins_dev`, no solo antes.

Pendiente de commit (no se hace commit salvo petición explícita del
usuario).

## #6 cositt_backend_accent (nuevo módulo) — cerrado

Color de acento configurable (por compañía) para botones primarios,
checkboxes/radios e ítem de menú activo del backend. Investigado antes
de escribir código: `$o-brand-primary` es una variable Sass compilada
fija (no se puede tocar en runtime); Bootstrap 5 sí expone custom
properties por componente (`--btn-bg` etc., **sin** el prefijo `bs-`
estándar — Odoo compila su propio fork), y el navbar ya expone
`--NavBar-entry-*--active` con fallback.

**Bug CRITICAL real, encontrado en verificación manual, no en tests ni
en el primer code review**: el primer diseño reasignaba esas custom
properties directamente con `var(--cositt-backend-accent)` sin
fallback, confiando en el mismo mecanismo "inerte por defecto" ya
usado en `cositt_login_background`. Ese mecanismo NO es seguro cuando
se reasigna una custom property de OTRO componente (Bootstrap) en vez
de una propiedad normal — la cascada decide qué declaración de
`--btn-bg` gana ANTES de comprobar si su valor es válido, así que un
valor inválido no "cae de vuelta" a la declaración de Bootstrap que
perdió esa cascada. Resultado real: con el módulo recién instalado y
SIN configurar, todos los botones primarios del backend quedaban
invisibles. **HIGH relacionado**: `web_enterprise` (instalado en este
proyecto) fija `--NavBar-entry-*--active` con valores FIJOS
directamente sobre `.o_main_navbar` — un `:root` nunca le gana, mismo
patrón que ya rompió el fondo de login en una ronda anterior. Fix en
ambos: clase marcador `.o_cositt_backend_accent_active` en `<html>`
(añadida por JS solo con color configurado) envolviendo TODAS las
reglas, ancladas al elemento real (`.o_main_navbar`), no solo `:root`.
Memoria nueva:
`~/.claude/projects/-Users-juan-Desktop-12messes12apps/memory/feedback_css_custom_property_override_pattern.md`
para que sesiones futuras no repitan este patrón inseguro.

**Mismo bug encontrado también en `cositt_login_background`** (código
de esta misma sesión, sin commitear): el botón "Log in" quedaba
transparente sin acento configurado — confirmado en vivo
(`getComputedStyle(...).backgroundColor` → `rgba(0,0,0,0)` contra
`/web/login` real). Corregido moviendo la regla del botón/enlaces
DENTRO del `<style>` server-side ya condicionado por
`t-if="accent_color"` (en vez de vivir en el SCSS estático, siempre
presente) — el módulo no usa JS, así que la clase marcador de arriba
no aplica; el condicional server-side cumple el mismo papel. 38/38
tests tras el fix.

14/14 tests. Verificado en navegador real en dos rondas (antes y
después del fix): estado desactivado ahora normal, estado configurado
en verde (#0e9f6e) en botones/checkboxes/navbar de Ajustes. Manual PDF
generado con capturas de ambos estados.

## #7 cositt_company_favicon — cerrado

Favicon (PNG) + título del navegador personalizados por compañía, en
todo el sitio (backend, login, portal — sin restricción de ruta,
a diferencia de sus hermanos). Reutiliza `x_icon`/`title`, variables
QWeb que `web.layout` ya declara con fallback, vía `t-set="... or
title"` (nunca incondicional, para no pisar un título más específico
de otra ruta). Patch JS sobre `titleService` para que la marca
sobreviva a la navegación SPA del backend.

**Bug real encontrado en verificación manual**: el patch mezclaba la
marca con `{...parts, cositt_brand: brand}` en una sola llamada — JS
conserva el orden de inserción de claves y `setParts()` no mueve una
clave ya existente, así que el título salía "Marca - Vista" en vez de
"Vista - Marca" (la llamada inicial al arrancar insertaba la marca
primero, y se quedaba ahí para siempre). Corregido borrando y
reinsertando la clave en cada llamada. Solo se detectó navegando de
verdad dentro del backend (clic en menú), no en la carga inicial.

Code review: 1 MEDIUM real, encontrado y corregido — la precedencia del
`t-set` estaba invertida (`cositt_favicon_url or x_icon` daba prioridad
SIEMPRE a este módulo), pisando el título/favicon específico de
`/scoped_app` (página PWA "Añadir a la pantalla de inicio"). Corregido
a `x_icon or cositt_favicon_url` + test de regresión. 21/21 tests.
Manual PDF generado. Cerrado.
