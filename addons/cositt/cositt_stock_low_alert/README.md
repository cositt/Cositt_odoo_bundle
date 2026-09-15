# Cositt Stock Low Alert

## Qué hace

Añade un umbral de stock mínimo por producto ("Low Stock Threshold", en
la pestaña Inventory de la ficha de producto). Un cron diario crea una
actividad de recordatorio cuando el stock disponible cae a ese umbral o
por debajo, asignada al "Responsible" del producto (campo nativo de
Inventario).

## Problema que resuelve

Las Reglas de Reabastecimiento nativas de Odoo (`stock.warehouse.orderpoint`)
generan automáticamente una orden de compra o fabricación cuando el
stock baja de un mínimo — pero exigen tener configurada una ruta
(compra/fabricación) y, normalmente, un proveedor. Muchos negocios
pequeños compran de forma manual y solo quieren un aviso, sin que se
genere ninguna orden en su nombre. Este módulo cubre ese caso: es un
simple recordatorio, complementario a las reglas de reabastecimiento, no
un sustituto.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde
Aplicaciones (requiere tener instalada la app Inventario). Sin
dependencias externas.

## Configuración

Ninguna adicional. El cron ("Cositt: Check low stock") se instala
activo, ejecutándose una vez al día.

## Uso

Manual con capturas de pantalla: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

En la ficha de un producto, pestaña Inventory: rellena "Low Stock
Threshold" con la cantidad a partir de la cual quieres el aviso (0 =
desactivado, valor por defecto). El campo "Is Low Stock" de al lado
refleja el estado actual, calculado a partir del stock disponible real.

Asegúrate de que el producto tiene un "Responsible" asignado (campo
nativo, normalmente ya viene relleno con quien creó el producto): sin
responsable, el cron no puede asignar el aviso y se registra solo un
warning en el log del servidor, sin crear nada.

## Dependencias

- Community: sí, funciona igual en Community.
- Enterprise: no requerido.
- Python / APIs externas: ninguna.

## Seguridad

No añade modelos, ACL ni reglas de registro nuevas: usa
`product.template` con los permisos ya existentes de Inventario.

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- El umbral y el stock se evalúan a nivel de plantilla de producto
  (`product.template`), agregando todas las variantes. Para productos
  con variantes (talla, color...) el aviso no distingue variante
  concreta — pensado para el caso común de productos sin variantes.
- El aviso se revisa una vez al día (cron), no en tiempo real en cada
  movimiento de stock.
- Mientras el producto siga por debajo del umbral y nadie complete el
  recordatorio, no se duplica el aviso; pero si se marca como hecho sin
  reponer stock, el cron del día siguiente crea uno nuevo — es
  intencional (sigue avisando hasta que se repone), no un error.
