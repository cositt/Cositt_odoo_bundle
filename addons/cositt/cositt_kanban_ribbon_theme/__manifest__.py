{
    "name": "Cositt Kanban Ribbon Theme",
    "version": "19.0.1.0.0",
    "summary": "Ribbon de color en tarjetas kanban de los modelos que elijas",
    "description": """
Añade un ribbon (banda de color en la esquina) a las tarjetas kanban de
los modelos que el administrador elija, usando el campo `color` (u
otro Integer) que ya tenga ese modelo — el mismo mecanismo estándar del
selector de color nativo de Odoo (menú "Establecer color" en las
tarjetas). No inventa una paleta nueva: reutiliza los mismos 12 colores
y las mismas clases (`o_colorlist_item_color_N`) que ya usa ese
selector, así que el ribbon combina siempre con el resto de la UI,
incluido modo oscuro.

Sin modelo nuevo por cada vista, sin tocar ninguna plantilla OWL: un
único patch de una función ya existente (`KanbanRecord.getRecordClasses`)
más CSS. Cero RPC por render: la lista de modelos configurados viaja
una vez en la sesión inicial (`session_info`), igual que ya hacen
`cositt_home_wallpaper` y `cositt_login_background`.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [
        "security/ir.model.access.csv",
        "views/cositt_kanban_ribbon_rule_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cositt_kanban_ribbon_theme/static/src/kanban/kanban_ribbon.scss",
            "cositt_kanban_ribbon_theme/static/src/kanban/kanban_ribbon_patch.js",
        ],
    },
    "installable": True,
    "application": False,
}
