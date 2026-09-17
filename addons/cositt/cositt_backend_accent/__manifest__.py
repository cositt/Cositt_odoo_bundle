{
    "name": "Cositt Backend Accent",
    "version": "19.0.1.0.0",
    "summary": "Color corporativo de acento para botones y elementos activos del backend",
    "description": """
Aplica un color de acento configurable (por compañía) a los botones
primarios y a los elementos activos del backend de Odoo (ítem de menú
seleccionado, checkboxes, radio buttons) — sin instalar un theme
completo ni recompilar SCSS.

Reutiliza las custom properties CSS que Bootstrap 5 y el propio core de
Odoo ya exponen en tiempo de ejecución (`--bs-btn-bg` por componente,
`--NavBar-entry-backgroundColor--active` a nivel de navbar,
`accent-color` nativo del navegador para checkboxes/radios) en vez de
inventar selectores propios o recompilar `$o-brand-primary` (una
variable Sass, fija en el bundle compilado, no ajustable en runtime).
Cero JavaScript de terceros, cero RPC adicional: el color viaja una vez
en `session_info()`, igual que `cositt_home_wallpaper`,
`cositt_login_background` y `cositt_kanban_ribbon_theme`.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cositt_backend_accent/static/src/backend_accent/backend_accent.scss",
            "cositt_backend_accent/static/src/backend_accent/backend_accent.js",
        ],
    },
    "installable": True,
    "application": False,
}
