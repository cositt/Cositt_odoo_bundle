{
    "name": "Cositt Quick WhatsApp",
    "version": "19.0.1.0.0",
    "summary": "Abre una conversación de WhatsApp con un contacto en un clic",
    "description": """
Añade un acceso directo junto al teléfono de cada contacto para abrir una
conversación de WhatsApp (wa.me), sin necesidad de integración oficial de
WhatsApp Business ni de guardar el número en ningún formato especial.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Contacts",
    "license": "LGPL-3",
    # phone_validation aporta phone_sanitized, que se usa para normalizar
    # el número antes de construir el enlace wa.me.
    "depends": ["contacts", "phone_validation"],
    "data": [
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
}
