# Cositt Attachment Lock

## Qué hace

Interruptor global: mientras esté activado, **nadie sin permiso especial
puede eliminar un adjunto vinculado a un registro** (factura, contacto,
proyecto, tarea...), ni desde la interfaz ni por RPC directo — el
bloqueo vive en el propio `unlink()` de `ir.attachment`, no en un botón
ocultado en la vista. Los administradores (grupo "Ajustes") pueden
seguir eliminando adjuntos sin configuración adicional.

## Investigación previa (antes de tocar `unlink()`)

Se investigó el ciclo de vida interno de adjuntos de Odoo 19 antes de
escribir el override, como exigía el encargo:

- **`@api.ondelete(at_uninstall=False)`** es el mecanismo que usa el
  propio Odoo para este tipo de regla (ver
  `account/models/ir_attachment.py`, que bloquea borrar adjuntos de un
  rastro de auditoría restringido con exactamente este decorador). Se
  eligió deliberadamente en vez de sobrescribir `unlink()` a mano: un
  override manual arriesga romper el borrado durante la desinstalación
  de otros módulos (deja basura en la base), mientras que
  `@api.ondelete` está pensado para desactivarse solo en ese caso
  (`at_uninstall=False`, la opción recomendada "casi siempre" según la
  propia documentación del decorador).
- **Paquetes de assets** (los `.js`/`.css` compilados que aparecen en
  Ajustes > Técnico > Adjuntos con "Resource Model" = `ir.ui.view`):
  verificado en `base/models/assetsbundle.py` que Odoo los crea y
  limpia siempre con `with_user(SUPERUSER_ID)` / `.sudo()`. Por eso la
  condición de exención más importante es `self.env.su` (contexto de
  superusuario): un usuario normal por RPC nunca tiene `env.su=True`,
  así que esto no abre ningún atajo real para nadie, solo deja pasar lo
  que Odoo ya hace internamente con privilegios elevados.
- **Adjuntos auto-generados** (el valor almacenado de un campo binario
  concreto, p. ej. un PDF de factura regenerado): se detectan por tener
  `res_field` relleno — no son algo que un humano haya adjuntado a
  mano, así que quedan fuera del alcance de la protección.
- **Adjuntos temporales/sin registro** (`res_model` vacío, p. ej. un
  adjunto subido en un compositor antes de guardar el registro): fuera
  del alcance también.

Solo queda protegido lo que de verdad importa proteger: un adjunto con
`res_model` propio y sin `res_field`, eliminado por un usuario normal
sin privilegios elevados — el caso de "alguien borra sin querer un
documento importante del chatter".

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde
Aplicaciones. Sin dependencias externas.

## Uso

1. Activa la protección: **Ajustes → Técnico → Parámetros del sistema**,
   busca `cositt_attachment_lock.enabled` y cámbialo a `True` (el
   módulo lo deja creado en `False` al instalar).
2. A partir de ahí, cualquier usuario que no sea Administrador (grupo
   "Ajustes") recibirá un aviso claro si intenta eliminar un adjunto
   normal — no podrá completarlo.
3. Para dar el permiso de eliminar igualmente a alguien que no es
   Administrador: **Ajustes → Usuarios → (usuario) → Otros permisos**,
   añade el grupo **"Cositt Attachment Lock / Puede eliminar adjuntos
   protegidos"**.
4. Para desactivar la protección, vuelve a poner el parámetro en
   `False`.

Los intentos bloqueados quedan registrados en el log del servidor
(usuario, id de adjunto, nombre) — no se creó un modelo de auditoría
aparte para esto, se consideró innecesario para el alcance de este MVP.

## Nota sobre `sudo()`

Una única línea usa `sudo()`: leer el valor del parámetro de
configuración global (`ir.config_parameter`). Es el mismo patrón que
usa internamente cualquier campo de `res.config.settings` con
`config_parameter=` — no decide nada sensible por sí solo, solo si la
protección está activada o no. El test
`test_module_only_uses_sudo_for_config_param` verifica que se mantiene
en exactamente 1 uso.
