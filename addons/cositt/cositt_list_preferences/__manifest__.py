{
    "name": "Cositt List Preferences",
    "version": "19.0.1.0.0",
    "summary": "Guarda qué columnas opcionales tienes activadas en cada lista, por usuario, en el servidor",
    "description": """
Odoo ya deja mostrar/ocultar columnas opcionales en cualquier vista de
lista, pero esa elección solo se guarda en el localStorage del propio
navegador — y ni siquiera por usuario: dos personas que compartan
navegador comparten la misma preferencia, y cambiar de dispositivo o
borrar datos del navegador la pierde. Este módulo mueve esa única
pieza al servidor (por usuario, no por navegador), sin tocar ninguna
plantilla ni el resto del comportamiento de la lista: mismo cuadro de
columnas de siempre, ahora recordado también en otro dispositivo.
No toca el ancho de columnas ni el orden de la lista — investigado
antes de empezar: ninguno de los dos se guarda hoy en ningún sitio
(ni siquiera en localStorage), así que quedan fuera del alcance de
este módulo (ver README).
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cositt_list_preferences/static/src/list_renderer/*.js",
        ],
    },
    "installable": True,
    "application": False,
}
