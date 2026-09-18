{
    "name": "Cositt Announcement Banner",
    "version": "19.0.1.0.0",
    "summary": "Banner superior configurable para avisos internos del backend",
    "description": """
Muestra una barra de aviso fija en la parte superior del backend
(mensaje + estilo info/éxito/aviso/urgente, configurable por compañía),
visible para todos los usuarios internos hasta que la cierren. Pensado
para comunicar mantenimientos programados, cambios de proceso u otros
avisos internos sin depender de email o Discuss.

Cero JavaScript de terceros, cero RPC adicional: el mensaje viaja una
vez en session_info(), igual que cositt_backend_accent y
cositt_kanban_ribbon_theme. Solo backend — no afecta a /web/login ni al
frontend público.
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
            "cositt_announcement_banner/static/src/announcement_banner/announcement_banner.scss",
            "cositt_announcement_banner/static/src/announcement_banner/announcement_banner.js",
            "cositt_announcement_banner/static/src/announcement_banner/announcement_banner.xml",
        ],
    },
    "installable": True,
    "application": False,
}
