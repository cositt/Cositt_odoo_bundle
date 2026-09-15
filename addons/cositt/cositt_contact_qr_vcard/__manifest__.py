{
    "name": "Cositt Contact QR vCard",
    "version": "19.0.1.0.0",
    "summary": "Genera un código QR con la vCard del contacto para compartir su tarjeta digital",
    "description": """
Añade un código QR en la ficha de cada contacto, generado localmente a
partir de sus datos (nombre, empresa, cargo, teléfono, email, dirección,
web) en formato vCard 3.0. Al escanearlo con la cámara de un móvil, el
contacto se puede añadir directamente a la agenda, sin enviar ningún dato
a un servicio externo.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Contacts",
    "license": "LGPL-3",
    "depends": ["contacts"],
    "external_dependencies": {
        "python": ["qrcode"],
    },
    "data": [
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
}
