# Cositt HR Document Expiry

## Qué hace

Añade una pestaña "Documents" en la ficha de cada empleado, con una
lista de documentos (DNI/NIE, permiso de trabajo, carné de conducir, o
cualquier otro que se necesite) con fecha de caducidad. Un cron diario
crea automáticamente una actividad de recordatorio antes de que caduque
cada documento, sin duplicar avisos ya abiertos.

## Problema que resuelve

Los documentos de un empleado (permiso de trabajo, carné de conducir
para puestos que lo requieren, etc.) caducan y es fácil que pase
desapercibido hasta que ya es tarde. Este módulo lo convierte en un
recordatorio automático en vez de depender de que alguien lo recuerde a
mano.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde
Aplicaciones (requiere tener instalada la app Empleados). Sin
dependencias externas.

## Configuración

Ninguna adicional. El cron ("Cositt: Check employee document expiry")
se instala activo, ejecutándose una vez al día.

## Uso

Manual con capturas de pantalla: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

En la ficha de un empleado, pestaña "Documents": añade una línea con el
nombre del documento, su fecha de caducidad, y cuántos días antes quieres
el aviso (30 por defecto). El estado (Valid / Expiring soon / Expired) se
actualiza solo.

Cuando un documento entra en la ventana de aviso (o ya caducó), el cron
diario crea una actividad "Por hacer" asignada al propio empleado (si
tiene usuario) o a su responsable directo (si no lo tiene). Si ninguno de
los dos tiene usuario, se registra un aviso en el log del servidor y no
se crea actividad — no bloquea ni rompe nada.

## Dependencias

- Community: sí, funciona igual en Community.
- Enterprise: no requerido.
- Python / APIs externas: ninguna.

## Seguridad

No añade grupos nuevos: el acceso al nuevo modelo
(`hr.employee.document`) se concede a `hr.group_hr_user`, el mismo grupo
base que ya gestiona el resto de la ficha de empleado.

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- El recordatorio solo sube un nivel en la cadena de mando (responsable
  directo del empleado); si ese responsable tampoco tiene usuario, no
  sigue subiendo más niveles.
- No reintenta con otro canal (email, etc.) si nadie tiene usuario: solo
  registra un aviso en el log del servidor.
