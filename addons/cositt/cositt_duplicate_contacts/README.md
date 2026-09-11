# Cositt Duplicate Contacts

## Qué hace

Odoo ya incluye un asistente de fusión de contactos que reasigna de forma
segura facturas, mensajes, actividades y demás documentos ligados a un
contacto antes de fusionarlo con otro. El problema: está escondido (sin
menú) y no permite agrupar por teléfono. Este módulo:

- Añade la opción "Teléfono" como criterio de búsqueda de duplicados
  (usando el número ya normalizado por Odoo, así "610 555 444" y
  "+34 610 555 444" cuentan como el mismo).
- Añade un acceso directo "Detectar duplicados" en el menú de Contactos.

No reimplementa la fusión: usa el asistente nativo de Odoo tal cual.

## Problema que resuelve

Sin este módulo, detectar y fusionar duplicados exige conocer el truco
técnico de Odoo (seleccionar contactos en la lista → Acción → Fusionar) y
no cubre coincidencias por teléfono.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde Aplicaciones.
Sin dependencias externas, sin configuración.

## Configuración

Ninguna.

## Uso

Manual con capturas de pantalla: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

1. Contactos → Detectar duplicados.
2. Marcar los criterios a comprobar (Email, Teléfono, NIF/VAT...). Si se
   marca más de uno, solo se consideran duplicados los contactos que
   coincidan en **todos** los criterios marcados a la vez (así lo indica
   el propio asistente).
3. "Fusionar con revisión manual" (recomendado) muestra cada grupo de
   duplicados uno a uno, permite elegir el contacto destino y confirmar
   o saltar. "Fusionar automáticamente" los fusiona todos sin revisión.

## Dependencias

- Community: sí, funciona igual en Community.
- Enterprise: no requerido.
- Módulos Odoo: `contacts`, `phone_validation` (ambos estándar, se instalan
  solos si hace falta).
- Python / APIs externas: ninguna.

## Seguridad

No añade modelos ni permisos nuevos: usa el modelo y permisos ya
existentes del asistente de fusión de Odoo (`base`).

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- La fusión no tiene deshacer: revisar bien el contacto destino antes de confirmar.
- Marcar varios criterios a la vez es una búsqueda estricta (deben coincidir
  todos), no una búsqueda amplia (coincidir en cualquiera). Es el
  comportamiento nativo de Odoo, no algo específico de este módulo.
