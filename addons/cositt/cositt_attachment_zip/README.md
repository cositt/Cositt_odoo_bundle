# Cositt Attachment Zip

## Qué hace

Selecciona uno o varios adjuntos (de cualquier modelo: presupuesto, factura,
contacto, proyecto, tarea, ticket...) desde **Ajustes → Técnico → Adjuntos**
y descarga un único **ZIP** con una carpeta por registro de origen, sin
nombres de archivo duplicados dentro de cada carpeta. Filosofía: "Selecciono
varios adjuntos de uno o varios registros y obtengo un único ZIP ordenado".

## Problema que resuelve

Cuando hay que recopilar varios documentos sueltos de varios registros
distintos (por ejemplo, todos los DNI de una lista de empleados, o todas
las facturas PDF de varios pedidos) descargarlos uno a uno desde el
navegador es lento. Odoo no ofrece una forma genérica de empaquetarlos en
un ZIP organizado.

## Arquitectura

Enganchado **directamente sobre `ir.attachment`** (no sobre modelos de
negocio concretos), igual que `cositt_pdf_merge`: aparece en el menú
**Acción** al multi-seleccionar adjuntos en cualquier vista de lista de
`ir.attachment`. Se descartó a propósito el patrón de "modelo habilitado
por el administrador" usado en `cositt_mass_edit`, porque esta
funcionalidad no toca ningún campo de negocio — solo lee adjuntos ya
existentes — así que no hace falta configuración previa ni depender de
qué modelos decida exponer un administrador.

Sin dependencias externas: usa `zipfile` de la librería estándar de
Python (no hace falta ninguna librería adicional).

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde
Aplicaciones.

## Uso

1. Ve a **Ajustes → Técnico → Adjuntos** (o cualquier otra vista que liste
   `ir.attachment`).
2. Selecciona uno o varios adjuntos (pueden pertenecer a registros
   distintos).
3. Usa el menú **Acción → Descargar adjuntos (ZIP)**.
4. En el asistente verás un resumen (nº de adjuntos, nº de registros de
   origen, tamaño total) y podrás elegir el nombre del archivo ZIP.
5. Pulsa **Generar ZIP**: se genera el archivo, descargable directamente
   desde el propio asistente.

Dentro del ZIP, cada adjunto queda en una carpeta con el nombre del
registro al que pertenece (p. ej. `Pedro Sánchez/dni.pdf`). Los adjuntos
sin registro vinculado van a una carpeta "Sin registro vinculado". Si dos
adjuntos del mismo registro tienen el mismo nombre, el segundo se renombra
automáticamente (`factura.pdf`, `factura_2.pdf`...).

## Permisos

Sin `sudo()` en ningún punto: si no podrías leer un adjunto (o su registro
padre) a mano, tampoco aparece en el ZIP — se respetan los permisos y
`ir.rule` normales de `ir.attachment`/del modelo de cada registro.

## Límites de la descarga

Para evitar cargar una selección enorme en memoria sin aviso (y arriesgar
la estabilidad de un worker de Odoo), esta versión aplica dos límites,
verificados **antes** de leer el contenido de ningún adjunto (usa el
campo `file_size`, ya almacenado, en vez de cargar los binarios para
medir):

- Máximo **300 adjuntos** por descarga.
- Máximo **50 MB** de tamaño total (suma de `file_size` de los adjuntos
  seleccionados).

Si se supera cualquiera de los dos, se muestra un aviso claro pidiendo
reducir la selección, en vez de intentarlo de todos modos. Estos valores
son constantes en `models/ir_attachment.py`
(`MAX_ATTACHMENT_COUNT`, `MAX_TOTAL_SIZE_BYTES`) — ajustables si un
proyecto concreto necesita otro límite.

## Seguridad: nombres de carpeta/archivo

Los nombres de carpeta (basados en `display_name` del registro) y de
archivo (basados en `attachment.name`) se sanean antes de usarse como
ruta dentro del ZIP: se eliminan separadores de directorio (`/`, `\`) y
caracteres no válidos, y no se permite un componente compuesto solo por
puntos (`.`, `..`). Esto evita cualquier intento de "zip slip"/path
traversal a partir de un nombre de registro o de archivo manipulado.
