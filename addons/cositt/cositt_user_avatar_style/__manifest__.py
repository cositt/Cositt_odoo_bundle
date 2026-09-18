{
    "name": "Cositt User Avatar Style",
    "version": "19.0.1.0.0",
    "summary": "Paleta de marca para los avatares con iniciales que genera Odoo",
    "description": """
Odoo ya genera automáticamente un avatar con iniciales y color de fondo
para cualquier contacto/empleado/registro sin foto propia (mecanismo
`avatar.mixin` del core) — pero el color se elige al azar (una función
hash sobre el nombre), sin relación con la identidad visual de la
empresa.

Este módulo reemplaza ESE color aleatorio por uno elegido de una
paleta de marca configurable por compañía: cada persona sigue teniendo
siempre el mismo color (determinista por su nombre, como ya hace
Odoo), pero ahora siempre dentro de los colores que la empresa elija —
mismo aspecto uniforme en toda la organización.

Cero canvas, cero JavaScript: el override vive en el propio mecanismo
de generación de SVG del core (`avatar.mixin`), así que aplica por
igual a cualquier modelo que lo use (Contactos, Empleados...), no solo
a uno en particular.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["base_setup"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
}
