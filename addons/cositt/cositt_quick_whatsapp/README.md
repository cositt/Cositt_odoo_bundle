# Cositt Quick WhatsApp

## Qué hace

Añade un icono de WhatsApp junto al teléfono de cada contacto. Al pulsarlo,
abre `wa.me` en una pestaña nueva con el número ya normalizado, listo para
empezar a escribir. No requiere la integración oficial de WhatsApp Business
ni ninguna cuenta/API de pago.

## Problema que resuelve

Escribir a un cliente por WhatsApp normalmente exige copiar el teléfono,
abrir WhatsApp Web o el móvil, pegarlo y darle formato a mano. Este botón
lo hace en un clic.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde Aplicaciones.
Sin dependencias externas, sin configuración.

## Configuración

Ninguna. Si la compañía tiene un país configurado (Ajustes → Compañías), el
número se normaliza incluso sin escribir el prefijo de país (+34...); si no,
solo funciona bien con números ya escritos con prefijo.

## Uso

Manual con capturas de pantalla: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

1. Abrir cualquier contacto con teléfono.
2. Pulsar el icono de WhatsApp junto al teléfono.
3. Se abre `wa.me` en una pestaña nueva, ya con el número correcto.

## Dependencias

- Community: sí, funciona igual en Community.
- Enterprise: no requerido.
- Módulos Odoo: `contacts`, `phone_validation` (ambos estándar).
- Python / APIs externas: ninguna. No usa la API de WhatsApp Business.

## Seguridad

No añade modelos ni permisos nuevos: el botón hereda los permisos ya
existentes de la ficha de contacto (si un usuario puede ver el contacto,
puede usar el botón).

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- Solo está en la ficha de Contactos por ahora. Backlog: acceso directo
  también desde CRM (oportunidades) y Ventas (presupuestos/pedidos) — se
  dejará como módulo(s) puente opcional(es) más adelante, para no forzar
  a instalar CRM/Ventas solo por este botón si la empresa no los usa.
- No sustituye a WhatsApp Business API: es un enlace directo a `wa.me`,
  pensado para uso manual, no para automatizar envíos masivos.
- Si el campo Teléfono tiene varios números (separados por `/`, `,`...) o
  una extensión, o si el número queda demasiado corto/largo tras limpiarlo,
  el botón avisa con un error en vez de abrir un enlace de WhatsApp que no
  funcionaría. En ese caso, corregir el teléfono para que tenga un único
  número completo.
