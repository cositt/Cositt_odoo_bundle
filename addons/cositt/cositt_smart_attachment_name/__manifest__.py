{
    "name": "Cositt Smart Attachment Name",
    "version": "19.0.1.0.0",
    "summary": "Renombra automáticamente los adjuntos usando datos del registro",
    "description": """
Define reglas simples (sin escribir código) para que los archivos que se
suban a un tipo de registro (facturas, presupuestos, contactos...) se
renombren solos usando datos del propio registro, por ejemplo:
"Factura_{name}_{partner_id.name}" -> Factura_F2026-00125_ACME.pdf
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/cositt_attachment_naming_rule_views.xml",
    ],
    "installable": True,
    "application": False,
}
