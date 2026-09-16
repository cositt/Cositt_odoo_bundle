{
    "name": "Cositt Home Wallpaper",
    "version": "19.0.1.0.0",
    "summary": "Fondo personalizado para el Home / menú de aplicaciones (Enterprise)",
    "description": """
Personaliza el Home Menu (la pantalla de aplicaciones) con una imagen de
fondo corporativa, color, overlay y desenfoque configurables — sin
instalar un theme completo y sin tocar el resto del backend (formularios,
listas, kanban, chatter, POS, website, portal, login siguen exactamente
igual). Configuración por compañía, en Ajustes Generales.

Requiere Odoo Enterprise: el Home Menu de pantalla completa (grid de
apps) es un componente exclusivo de `web_enterprise`
(`web_enterprise.HomeMenu`) — Community no tiene un equivalente de
pantalla completa, solo un desplegable pequeño en la barra de navegación
(investigado en el código fuente antes de escribir nada; ver README).
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["web_enterprise"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cositt_home_wallpaper/static/src/home_menu/*.scss",
            "cositt_home_wallpaper/static/src/home_menu/*.js",
        ],
    },
    "installable": True,
    "application": False,
}
