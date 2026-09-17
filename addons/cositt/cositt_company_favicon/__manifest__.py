{
    "name": "Cositt Company Favicon",
    "version": "19.0.1.0.0",
    "summary": "Favicon y título del navegador personalizados por compañía",
    "description": """
Personaliza el favicon (icono de la pestaña del navegador) y el título
de la pestaña con una imagen y un texto de marca propios, por
compañía — en todo el sitio: backend, /web/login y portal.

Reutiliza los puntos de extensión que `web.layout` ya declara para
esto (`x_icon`, `title`), pensados originalmente para apps PWA
"scoped" — investigado en el código fuente antes de escribir nada, ver
README. Para que el título de marca sobreviva a la navegación dentro
del backend (una SPA que recalcula `document.title` en cada cambio de
vista) también parchea el servicio `title` del webclient.
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
        "web.assets_backend": [
            "cositt_company_favicon/static/src/company_favicon/company_favicon.js",
        ],
    },
    "installable": True,
    "application": False,
}
