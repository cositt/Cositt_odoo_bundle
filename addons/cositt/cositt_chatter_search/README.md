# Cositt Chatter Search

## Qué hace

Amplía el **buscador de mensajes nativo del chatter** (icono de lupa,
disponible desde hace tiempo en Odoo 19 en el chatter de cualquier
modelo) para que también encuentre mensajes por **autor**: nombre de
usuario/contacto (`author_id`), remitente de email cuando no hay
contacto vinculado (`email_from`), o nombre de invitado
(`author_guest_id`, p. ej. mensajes de un chat de portal/website).

## Por qué este módulo es tan pequeño

Antes de escribir nada se investigó cómo Odoo 19 carga y pagina los
mensajes del chatter (tal y como pedía el encargo original). Resultado:
**Odoo 19 Community ya trae un buscador de chatter completo**, con
paginación real en servidor (no vuelca el historial entero al
navegador) — icono de lupa en `chatter.xml`, componente
`SearchMessageInput`, y `mail.message._message_fetch(..., search_term=...)`
en el servidor, genérico para cualquier modelo con `mail.thread` (pasa
por el controlador único `/mail/thread/messages`).

Ese buscador ya cubre: cuerpo del mensaje, asunto, nombre de adjuntos y
valores de seguimiento (cambios de campo). Lo único que **no** cubre es
el autor. Construir un buscador propio desde cero habría duplicado una
funcionalidad ya sólida — así que este módulo hace exactamente un
cambio quirúrgico: añade tres condiciones más al `OR` que ya construye
`_message_fetch` quando hay `search_term`. **No hace falta tocar ni un
componente OWL ni una plantilla**: como el mismo cuadro de búsqueda ya
existente manda el `search_term` al servidor, escribir "Juan" en esa
misma caja empieza a encontrar también los mensajes de Juan Pérez sin
ningún cambio de interfaz.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde
Aplicaciones. Depende solo de `mail` (ya viene con cualquier instalación
de Odoo).

## Uso

1. Abre el chatter de cualquier registro (contacto, factura, proyecto...).
2. Pulsa el icono de lupa ("Search Messages"), arriba a la derecha del
   chatter.
3. Escribe el nombre de una persona (usuario, contacto o remitente de
   email) en el mismo cuadro de búsqueda de siempre.
4. Los mensajes de esa persona aparecen igual que si hubieras buscado
   por contenido — con la misma paginación ("cargar más") que ya trae
   el buscador nativo.

## Nota sobre `sudo()`

Este archivo es una copia completa de `mail.message._message_fetch` del
core (no hay ningún punto de extensión para añadir una condición al
`OR` interno sin copiar el método entero — ver el comentario en el
propio código, con aviso de re-diferenciar en cada upgrade de Odoo). El
método original ya usa `sudo()` dos veces (nombre de adjunto y valores
de tracking). Este módulo añade **2 usos más**, con el mismo criterio ya
documentado por el propio core: resolver qué `author_id`/`author_guest_id`
coinciden por nombre no necesita el permiso de lectura del usuario sobre
`res.partner`/`mail.guest` — el acceso real lo decide el `search()` final
de `mail.message` (sin `sudo()`), que solo devuelve mensajes de hilos a
los que el usuario ya tiene acceso. Sin este `sudo()`, la búsqueda por
autor rompía con `AccessError` para cualquier usuario sin el grupo
interno (p. ej. un usuario público/portal) en cuanto el término de
búsqueda pasaba por el traversal `author_guest_id.name` — encontrado por
el propio test de permisos de este módulo, no una suposición.
El test `test_module_only_uses_sudo_inherited_or_justified` verifica que
el número de usos se mantiene exactamente en 4 (2 heredados + 2 nuevos).

## Permisos

La búsqueda por autor respeta el mismo control de acceso que el resto
del método: si no tendrías acceso a un mensaje (porque no puedes leer
el registro al que pertenece), tampoco aparece en el resultado de la
búsqueda, autor incluido.
