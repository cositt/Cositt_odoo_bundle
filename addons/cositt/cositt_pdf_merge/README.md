# Cositt PDF Merge

## Qué hace

Combina varios archivos PDF adjuntos a un mismo registro (presupuesto,
factura, contacto, proyecto, tarea, ticket... cualquier modelo que use
adjuntos) en un único PDF, respetando el orden que elijas. Filosofía:
"Selecciono varios PDF asociados a un registro y obtengo un único PDF
combinado."

## Problema que resuelve

Es habitual que un mismo registro acumule varios PDF sueltos (presupuesto,
ficha técnica, condiciones...) que hay que enviar juntos. Odoo no ofrece
una forma genérica de combinarlos en un solo archivo sin recurrir a
herramientas externas.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde
Aplicaciones. Sin dependencias externas: reutiliza el propio mecanismo de
fusión de PDF de Odoo (`ir.actions.report._merge_pdfs`, el mismo que usa
el envío por lote de informes/facturas), que ya usa `PyPDF2` incluido en
la imagen oficial de Odoo.

## Uso

Manual con capturas de pantalla: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

1. Sube tus PDF al registro como adjuntos normales (chatter, formulario...).
2. Ve a **Ajustes → Técnico → Adjuntos** (o cualquier otra vista que liste
   `ir.attachment`, p. ej. filtrando por "Documento relacionado").
3. Selecciona uno o varios adjuntos del registro y usa el menú **Acción →
   Combinar PDF**. Basta con seleccionar un adjunto: el asistente carga
   automáticamente TODOS los PDF de ese mismo registro.
4. En el asistente, marca los PDF que quieres incluir y ordénalos
   arrastrando (icono de agarre).
5. Escribe opcionalmente un nombre para el resultado.
6. Pulsa **Generar PDF**: se genera el archivo, descargable directamente
   desde el propio asistente.
7. Si quieres conservarlo, deja marcada la opción "Guardar como adjunto
   del registro" (marcada por defecto): se añade como un nuevo adjunto
   del registro original.

## Por qué el punto de entrada está en "Adjuntos" y no en cada formulario

El módulo debe funcionar igual para cualquier modelo (Ventas, Facturación,
Contactos, Proyecto...) sin añadir esos módulos como dependencia. El panel
de adjuntos del chatter (icono del clip) es un widget sin menú de
acciones ni selección múltiple, así que no hay forma estándar de
engancharse ahí sin JavaScript a medida. Enganchar la acción directamente
sobre `ir.attachment` (que sí es una vista lista/kanban estándar con
selección múltiple) consigue el mismo resultado de forma 100% genérica,
sin menús nuevos y sin tocar la vista de ningún otro módulo.

## Dependencias

- Community: sí, funciona igual en Community.
- Enterprise: no requerido.
- Python / APIs externas: ninguna nueva. Usa `PyPDF2`, ya incluido en la
  imagen oficial `odoo:19.0` (es el mismo que usa el core de Odoo).

## Seguridad

- No usa `sudo()` en ningún punto. La búsqueda de adjuntos y la lectura de
  su contenido usan el usuario actual: si no tienes acceso al registro (o
  a `ir.attachment` para ese registro), Odoo deniega el acceso igual que
  en cualquier otra pantalla.
- El PDF combinado se crea con el usuario actual: si no tienes permiso de
  creación de adjuntos sobre ese registro, la creación falla igual que
  subir un adjunto a mano.
- No se combinan adjuntos de registros distintos en una misma operación
  (se exige que todos pertenezcan al mismo registro).

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- Solo combina adjuntos ya subidos a un registro guardado (con modelo e
  ID); no genera el PDF a partir de un formulario todavía sin guardar.
- No permite dividir un PDF en páginas sueltas ni reordenar páginas
  dentro de un mismo PDF (eso es un caso de uso distinto, más cercano al
  editor de "Documentos" de Enterprise); este módulo solo concatena
  documentos completos.
- Un PDF protegido con contraseña se trata como "dañado" (no se puede
  leer sin la contraseña) y se rechaza con un mensaje claro, en vez de
  pedir la contraseña.

## Ejemplo práctico

Un presupuesto tiene adjuntos `presupuesto.pdf`, `ficha_tecnica.pdf` y
`condiciones.pdf`. Desde Ajustes → Técnico → Adjuntos, seleccionas
cualquiera de ellos → Acción → Combinar PDF. En el asistente marcas los
tres, los ordenas (presupuesto, ficha técnica, condiciones), escribes
`documentacion_completa` como nombre y pulsas Generar PDF. Obtienes
`documentacion_completa.pdf` con las páginas de los tres documentos en
ese orden, descargable al momento y guardado como nuevo adjunto del
presupuesto.
