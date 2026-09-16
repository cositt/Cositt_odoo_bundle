# Cositt Activity Digest

## Qué hace

Añade un menú **"Mis Actividades"** que reúne, en un solo sitio, las
actividades programadas (recordatorios, llamadas, tareas de seguimiento...)
en **cualquier modelo** de Odoo: facturas, contactos, activos, proyectos...
Con filtros ya listos de "Vencidas", "Hoy", "Mañana", "Esta semana", vista
lista/kanban/calendario, y agrupables por modelo/usuario/tipo. Además,
añade **"Posponer"**: mueve varias actividades seleccionadas un número
cualquiera de días (o negativo, para adelantarlas) de una sola vez.

## Problema que resuelve

Odoo ya trae internamente esta vista completa (`mail.mail_activity_action_my`,
la que usa el propio widget del reloj y la paleta de comandos Ctrl+K), pero
**no la enlaza a ningún menú**: un usuario normal no tiene forma de
encontrarla sin saber que existe. Lo único que hace falta es exponerla.

Sobre posponer en lote: Odoo ya trae accesos rápidos nativos para mover
varias actividades seleccionadas a "Hoy", "Mañana" o "Próxima semana" (tres
fechas fijas). Lo que no permite es posponerlas un número **cualquiera** de
días (p. ej. "+10 días" o "+3 semanas") ni adelantarlas — solo esas tres
opciones fijas hacia delante.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde
Aplicaciones. Sin dependencias externas.

## Uso

Manual con capturas de pantalla: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

1. Entra en el nuevo menú **Mis Actividades**.
2. Verás tus actividades vencidas y de hoy (filtro por defecto), de
   cualquier modelo. Cambia de filtro/vista según necesites.
3. Selecciona una o varias actividades (checkboxes de la lista).
4. Menú **Acción → Posponer**.
5. Indica cuántos días sumar (o un número negativo para adelantarlas) y
   confirma.

## Dependencias

- Community: sí, funciona igual en Community (`mail` es Community).
- Enterprise: no requerido.
- Python / APIs externas: ninguna.

## Seguridad

- No usa `sudo()` en ningún punto. Abrir el asistente y posponer
  actividades usa el usuario actual: si no tienes acceso al registro al
  que está vinculada una actividad, Odoo deniega la operación igual que
  en cualquier otra pantalla.
- No se crea ningún modelo de negocio nuevo ni se tocan permisos
  existentes de `mail.activity`: solo se reutiliza la acción nativa y se
  añade una acción de escritura en lote sobre `date_deadline`.

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- "Posponer" solo cambia la fecha límite (`date_deadline`); no cambia el
  usuario asignado, el tipo de actividad ni ningún otro campo.
- El menú se añade como una entrada de nivel superior (como los pequeños
  módulos de productividad tipo "To-do"): no hace falta que cada app
  tenga un botón propio para actividades, ya son transversales a todos
  los modelos por diseño de Odoo.

## Ejemplo práctico

Un usuario vuelve de dos semanas de baja y tiene 5 actividades vencidas,
repartidas entre dos contactos y una factura. En vez de abrir cada una y
reprogramarla a mano (o usar el botón nativo "Próxima semana", que no le
da margen suficiente), entra en Mis Actividades, filtra por "Vencidas",
selecciona las 5, Acción → Posponer → 10 días, y las 5 quedan
reprogramadas de una sola vez.
