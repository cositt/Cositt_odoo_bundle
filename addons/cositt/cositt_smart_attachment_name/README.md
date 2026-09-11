# Cositt Smart Attachment Name

## Qué hace

Renombra automáticamente los archivos que se suben a un tipo de registro
(facturas, presupuestos, contactos, proyectos...) usando datos del propio
registro, sin escribir código. Ejemplo: una regla con el patrón
`Factura_{name}_{partner_id.name}` convierte `scan001.pdf` en
`Factura_F2026-00125_ACME.pdf` al subirlo a una factura.

## Problema que resuelve

Los archivos que suben los usuarios (escaneos, fotos del móvil...) suelen
llegar con nombres como `IMG_2024.jpg` o `scan(3).pdf`, que no dicen nada
y son difíciles de encontrar luego. Odoo ya permite nombrar así los PDF que
él mismo genera al imprimir un informe (Ajustes → Técnico → Informes,
campo "Nombre del informe"), pero ese campo usa expresiones Python y solo
afecta a los informes generados por Odoo, no a los archivos que suben los
usuarios a mano.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde Aplicaciones.
Sin dependencias externas.

## Configuración

Ajustes → Técnico → Nombrado de adjuntos (Cositt) → Nuevo:

- **Modelo**: a qué tipo de registro se aplica (Factura, Contacto...).
- **Patrón**: texto libre con `{campo}` o `{campo.subcampo}` para insertar
  datos del registro, por ejemplo `Factura_{name}_{partner_id.name}`.
- La extensión del archivo (`.pdf`, `.jpg`...) se conserva siempre.
- Solo puede haber una regla activa por modelo.

Requiere acceso de Ajustes/Técnico (perfil administrador).

## Uso

Manual con capturas de pantalla: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

Una vez configurada una regla, no hay que hacer nada más: cualquier archivo
que se suba a un registro de ese modelo (desde el chatter, un widget de
adjuntos, etc.) se renombra solo en el momento de subirlo.

## Dependencias

- Community: sí, funciona igual en Community.
- Enterprise: no requerido.
- Python / APIs externas: ninguna.

## Seguridad

- Configurar reglas requiere el grupo Ajustes/Técnico (administrador).
- La resolución de `{campo}` usa el mecanismo estándar de Odoo para leer
  campos (`mapped`), nunca ejecuta código ni expresiones Python: si el
  campo no existe, simplemente se omite esa parte del nombre, sin fallar.
- Un adjunto siempre se sube aunque la regla esté mal escrita: un patrón
  con un campo inválido no bloquea la subida, solo deja de aportar esa
  parte del nombre.

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- Solo renombra adjuntos que ya se suben directamente vinculados a un
  registro guardado (con modelo y ID). Un archivo subido al chatter de un
  registro *todavía sin guardar* puede no recibir el nuevo nombre hasta
  que el registro se guarde y el adjunto se vuelva a vincular.
- Si el modelo ya genera adjuntos con nombre automático por su cuenta
  (como el PDF de una factura, vía "Nombre del informe" en Ajustes
  técnicos), una regla configurada aquí para ese mismo modelo también
  renombrará esos archivos, pudiendo sustituir ese nombre. Si no se
  quiere ese efecto, no crear una regla para modelos donde ya se use esa
  configuración de Odoo.
- Solo una regla activa por modelo (para mantenerlo simple): no permite
  reglas distintas según el tipo de documento dentro de un mismo modelo.
