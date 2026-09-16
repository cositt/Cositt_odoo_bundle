# Cositt Maintenance QR Asset

## Qué hace

Añade un código QR en la ficha de cada activo de **Mantenimiento**
(`maintenance.equipment`), generado localmente a partir de sus propios
datos: nombre, categoría, modelo, número de serie, propietario, técnico
asignado, proveedor y fecha de garantía. Al escanearlo con la cámara de
un móvil se lee la ficha directamente como texto — sin necesitar
conexión a internet ni sesión abierta en Odoo.

## Problema que resuelve

Un equipo físico (impresora, router, máquina...) suele acabar con una
etiqueta de inventario que solo tiene un número interno, obligando a
buscarlo en Odoo para saber qué es. Este módulo genera una etiqueta con
QR que se puede imprimir y pegar en el propio equipo: cualquiera que la
escanee (tenga o no acceso a Odoo) ve al instante de qué activo se trata.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde
Aplicaciones. Requiere el módulo **Mantenimiento** (`maintenance`) de
Odoo, instalado automáticamente como dependencia.

## Uso

Manual con capturas de pantalla: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

1. Abre un activo en Mantenimiento → Activos.
2. Ve a la pestaña **QR**.
3. El código se genera solo, con los datos ya rellenados del activo.
4. Escanéalo con la cámara de cualquier móvil, o imprímelo para pegarlo
   en el equipo.

## Contenido del QR

Texto plano, no un formato estándar (a diferencia de una vCard de
contacto, no existe un formato equivalente para activos físicos):

```
EQUIPO: Impresora 3D
Categoría: Electrónica
Modelo: Prusa MK4
Nº Serie: SN-001
Propietario: Ana Torres
Técnico: Pedro Sánchez
Proveedor: Proveedor SL
Garantía hasta: 2027-01-01
```

Solo se incluyen las líneas de los campos que el activo tenga rellenos.

## Dependencias

- Community: sí, funciona igual en Community (`maintenance` es un
  módulo Community, no requiere Enterprise).
- Enterprise: no requerido.
- Python: `qrcode`, ya incluido en la imagen oficial `odoo:19.0` (mismo
  hallazgo que `cositt_contact_qr_vcard`: lo usa el propio core de Odoo
  para otros QR, como el de `auth_totp`).

## Seguridad

- El QR se genera localmente, sin enviar ningún dato a un servicio
  externo.
- El campo es un campo calculado (`compute`), no almacenado: siempre
  refleja los datos vigentes del activo y respeta los mismos permisos
  que el resto de la ficha (si no tienes acceso al activo, no ves su
  ficha ni, por tanto, su QR).
- Un fallo puntual generando el QR (por ejemplo, un problema de acceso
  a un campo relacionado en un escenario multi-compañía) nunca rompe la
  carga del formulario: el campo simplemente queda vacío.

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- No almacenado (`store=False`): pensado para el formulario (un
  registro a la vez), no para listas/kanban/exportación masiva, donde
  generaría un PNG por fila en cada lectura.
- El QR contiene texto plano legible, no un enlace a la ficha en Odoo:
  escanearlo no abre el registro, solo muestra sus datos. Es una
  decisión deliberada para que la etiqueta sea útil también para quien
  no tiene acceso a Odoo (ver notas de arquitectura en `CLAUDE.md`).
- No incluye los "Properties" personalizadas del activo
  (`equipment_properties`), solo los campos estándar de Mantenimiento.

## Ejemplo práctico

Un router de red está registrado como activo con categoría "Redes",
modelo "RT-500", número de serie "SN-2024-118" y propietario "IT
Cositt". Al abrir su ficha y entrar en la pestaña QR aparece el código
ya generado; se imprime y se pega en el propio router. Cualquier
persona que lo escanee con la cámara del móvil ve directamente:
"EQUIPO: Router Principal / Categoría: Redes / Modelo: RT-500 / Nº
Serie: SN-2024-118 / Propietario: IT Cositt", sin necesitar abrir Odoo.
