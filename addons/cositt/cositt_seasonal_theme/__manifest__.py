{
    "name": "Cositt Seasonal Theme",
    "version": "19.0.1.0.0",
    "summary": "Decoraciones estacionales ligeras y programables para el backend",
    "description": """
Icono temático en la barra de navegación (Navidad, Feria, Cumpleaños o
Campaña personalizada) y, opcionalmente, partículas decorativas
animadas (copos, flores, velas, confeti de colores) flotando sobre el
backend — configurable por compañía, con rango de fechas opcional para
activar/desactivar solo.

Cero JavaScript de terceros, cero canvas, cero RPC adicional: el tema
viaja una vez en session_info(), igual que cositt_announcement_banner
y cositt_backend_accent. El icono se registra como ítem de systray (el
mismo mecanismo que usan Mensajes/Actividades) para no competir por
ninguna esquina fija de la pantalla ya ocupada por elementos nativos
(indicador de carga, notificaciones). Las partículas son puro CSS
(@keyframes), sin bucle de JS por fotograma, y respetan
prefers-reduced-motion.
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
            "cositt_seasonal_theme/static/src/seasonal_theme/theme_data.js",
            "cositt_seasonal_theme/static/src/seasonal_theme/systray_icon.scss",
            "cositt_seasonal_theme/static/src/seasonal_theme/systray_icon.js",
            "cositt_seasonal_theme/static/src/seasonal_theme/systray_icon.xml",
            "cositt_seasonal_theme/static/src/seasonal_theme/particles.scss",
            "cositt_seasonal_theme/static/src/seasonal_theme/particles.js",
            "cositt_seasonal_theme/static/src/seasonal_theme/particles.xml",
        ],
    },
    "installable": True,
    "application": False,
}
