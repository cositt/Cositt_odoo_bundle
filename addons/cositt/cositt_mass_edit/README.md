# Cositt Mass Edit

## Qué hace

Selecciona varios registros en una vista de lista (contactos, o cualquier
otro modelo que habilite un administrador) y cambia un campo en todos a
la vez — o lo vacía — sin abrir cada uno a mano.

## Problema que resuelve

Cambiar un mismo dato (el comercial asignado, una categoría, una
etiqueta de texto...) en decenas de registros uno por uno es lento y
propenso a errores. Odoo ya permite editar varios registros a la vez
*directamente en una lista editable*, pero solo si esa vista concreta
es editable y el campo ya es una columna visible. Este módulo añade un
asistente que funciona desde cualquier lista (editable o no) y deja
elegir cualquier campo seguro del modelo, no solo los que ya se ven
como columna.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde
Aplicaciones. Sin dependencias externas.

## Configuración

**Ajustes → Técnico → Edición masiva** (requiere grupo de
Administración/Técnico): lista de modelos donde aparece la acción.
Contactos (`res.partner`) viene habilitado de fábrica. Para añadir otro
modelo, crea una línea nueva con ese modelo — la acción "Edición
masiva" aparece al momento en su vista de lista. Quitar la línea la
desactiva.

## Uso

Manual con capturas de pantalla: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

1. En una vista de lista de un modelo habilitado, selecciona varios
   registros con las casillas.
2. Menú **Acción → Edición masiva**.
3. Elige el campo a cambiar (solo aparecen campos seguros — ver
   Seguridad).
4. Escribe el nuevo valor, o marca **Vaciar campo** (si el campo no es
   obligatorio).
5. **Aplicar**: todos los registros seleccionados quedan actualizados a
   la vez.

## Ejemplo

Seleccionas 50 contactos → Acción → Edición masiva → Campo: Comercial →
Valor: Jorge → Aplicar. Los 50 contactos quedan asignados a Jorge.

## Dependencias

- Community: sí, funciona igual en Community.
- Enterprise: no requerido.
- Python / APIs externas: ninguna.

## Seguridad

- **Lista blanca de campos, no lista negra**: solo se ofrecen campos de
  tipo `char`, `text`, `integer`, `float`, `boolean`, `selection`,
  `many2one`, `date` y `datetime` que además sean almacenados
  (`store=True`), no computados, no `related` y no de solo lectura.
  Se excluyen siempre los campos técnicos (`id`, `create_uid`,
  `create_date`, `write_uid`, `write_date`, `display_name`...).
  `many2many`, `one2many`, binarios y HTML quedan fuera del alcance de
  este módulo (ver Limitaciones).
- `fields_get()` del modelo ya filtra por los grupos del campo: un
  campo restringido a un grupo que el usuario no tiene, ni siquiera
  aparece en la lista de campos disponibles.
- El campo elegido se revalida en el servidor contra la lista blanca
  calculada al abrir el asistente (defensa en profundidad: el dominio
  del desplegable en la vista es solo UX, no la única barrera).
- La escritura se hace con una única llamada `write()` sobre todo el
  recordset seleccionado, sin `sudo()`: si el usuario no podría
  modificar un registro a mano (ACL, record rule, campo obligatorio
  vacío...), tampoco puede con este asistente — y al ser una sola
  llamada, si un registro falla, **no se aplica el cambio a ninguno**
  (todo o nada, sin dejar datos a medio actualizar).
- Habilitar modelos para edición masiva (Ajustes → Técnico) requiere el
  grupo de Administración (`base.group_system`).

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- No incluye `many2many` ni `one2many`: la semántica de "cambiar" una
  relación múltiple es ambigua (¿reemplazar todo, añadir, quitar?) y se
  ha dejado fuera a propósito para no complicar un asistente que debe
  seguir siendo simple. Tampoco incluye binarios ni HTML.
- Si la vista de lista de un modelo habilitado ya es editable y el
  campo que quieres cambiar es una columna visible, Odoo ya te deja
  seleccionar varias filas y editar una celda directamente ("¿Aplicar a
  los N registros seleccionados?") sin necesitar este módulo — es un
  atajo nativo más rápido para ese caso concreto. Este asistente cubre
  el resto: listas no editables, o campos que no son columna visible.
- Solo el administrador (grupo Técnico) decide qué modelos tienen la
  acción disponible; no hay forma de habilitarlo por usuario.
