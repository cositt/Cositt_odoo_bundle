# Cositt IBAN Validator

## Qué hace

Valida las cuentas bancarias que tienen forma de IBAN (formato, longitud
según el país, dígito de control) antes de guardarlas, para detectar
errores de transcripción al momento, no después.

## Problema que resuelve

Un IBAN mal copiado (un dígito de más, de menos, o transpuesto) suele
descubrirse solo cuando un banco rechaza una transferencia. Este módulo
avisa en el momento de guardar el dato en Odoo.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde Aplicaciones.
Sin dependencias externas, sin configuración.

**No requiere el módulo de Contabilidad.** Odoo trae de serie un módulo
oficial (`base_iban`) con validación de IBAN, pero exige instalar
`account` (Contabilidad); muchas empresas usan Odoo solo para Contactos,
CRM, etc. sin Contabilidad. Este módulo funciona directamente sobre
`res.partner.bank`, que ya viene en el núcleo de Odoo.

## Configuración

Ninguna.

## Uso

Manual con capturas de pantalla: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

Al guardar una cuenta bancaria (en un contacto, o donde se gestionen
cuentas bancarias) cuyo número tiene forma de IBAN, se valida
automáticamente. Si algo no cuadra, Odoo muestra un aviso explicando qué
falla (formato, longitud o dígito de control) antes de guardar.

Los números de cuenta que **no** tienen forma de IBAN (países que no lo
usan) no se tocan ni se fuerzan a este formato.

## Dependencias

- Community: sí, funciona igual en Community (de hecho, es el motivo de
  ser de este módulo: no depender de Contabilidad).
- Enterprise: no requerido.
- Python / APIs externas: ninguna.

## Seguridad

No añade modelos, campos ni permisos nuevos: solo valida un campo ya
existente (`acc_number`) con los permisos que ya tenía.

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- La tabla de longitudes esperadas cubre los países europeos habituales
  (SEPA); para un país IBAN no incluido en la tabla, se valida el formato
  y el dígito de control, pero no la longitud exacta.
- No verifica que el banco/sucursal exista realmente (eso requeriría una
  base de datos bancaria externa); solo valida la estructura matemática
  del número, que es lo que detecta errores de transcripción.
