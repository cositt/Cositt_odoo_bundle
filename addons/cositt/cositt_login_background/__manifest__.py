{
    "name": "Cositt Login Background",
    "version": "19.0.1.0.0",
    "summary": "Fondo personalizado para la pantalla de login (Community + Enterprise)",
    "description": """
Personaliza la pantalla de login de Odoo (/web/login) con una imagen de
fondo corporativa, color, overlay y desenfoque configurables — sin
instalar un theme completo y sin tocar el resto del frontend ni del
backend (formularios, listas, kanban, POS, website, portal y el Home
Menu siguen exactamente igual). Configuración por compañía, en Ajustes
Generales.

Renderizado 100% del lado del servidor (QWeb puro, sin JavaScript ni
RPC): el fondo se pinta directamente en el HTML de la pantalla de
login, sin parpadeo posible. Funciona igual en Community y en
Enterprise: la pantalla de login vive en el módulo base `web`
(`web.login_layout`), no en `web_enterprise` — investigado en el código
fuente antes de escribir nada (ver README).
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/webclient_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "cositt_login_background/static/src/login/login_background.scss",
        ],
    },
    "installable": True,
    "application": False,
}
