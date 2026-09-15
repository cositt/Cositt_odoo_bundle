# Cositt Contact QR vCard

## Qué hace

Añade una pestaña "Digital Card" en la ficha de cada contacto con un
código QR generado localmente, que contiene una vCard 3.0 (nombre,
empresa, cargo, teléfono, email, dirección, web). Al escanearlo con la
cámara de un móvil, el contacto se puede añadir directamente a la agenda.

## Problema que resuelve

Compartir los datos de contacto en una reunión o feria normalmente
implica dictarlos o mandar una tarjeta física. Este módulo genera una
tarjeta digital escaneable al momento, sin imprimir nada ni depender de
ningún servicio externo (todo el QR se genera en el propio servidor).

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde
Aplicaciones. Requiere la librería Python `qrcode`, ya incluida en la
imagen oficial `odoo:19.0` (la usa el propio core para el QR de doble
factor de autenticación, entre otros), así que no hace falta instalar
nada adicional en un entorno estándar.

## Configuración

Ninguna.

## Uso

Manual con capturas de pantalla: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

En la ficha de cualquier contacto (persona o empresa), pestaña "Digital
Card": el QR se genera y actualiza automáticamente según cambian los
datos del contacto (nombre, teléfono, email, dirección, web, cargo,
empresa). No requiere guardar el registro para verse.

## Dependencias

- Community: sí, funciona igual en Community.
- Enterprise: no requerido.
- Python: `qrcode` (ya presente en la imagen oficial `odoo:19.0`).
- APIs externas: ninguna. El QR se genera enteramente en el servidor, sin
  enviar ningún dato de contacto a un servicio externo.

## Seguridad

No añade modelos, ACL ni reglas de registro nuevas: usa el modelo
`res.partner` con los permisos que Odoo ya aplica de forma nativa sobre
contactos. El QR solo puede verse por quien ya tiene acceso de lectura a
la ficha del contacto.

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- El campo no se almacena en base de datos (se recalcula en cada
  lectura), por diseño: evita que el QR quede desactualizado si cambian
  los datos del contacto. No está pensado para usarse en vistas de lista
  o kanban con muchos registros a la vez.
- La vCard generada no incluye foto de perfil ni redes sociales.
