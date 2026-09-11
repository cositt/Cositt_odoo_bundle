{
    "name": "Cositt IBAN Validator",
    "version": "19.0.1.0.0",
    "summary": "Valida formato, longitud y dígito de control de cuentas IBAN",
    "description": """
Valida las cuentas bancarias con forma de IBAN (formato, longitud según el
país, dígito de control) antes de guardarlas, para detectar errores de
transcripción. No depende del módulo de Contabilidad: funciona con
res.partner.bank tal cual viene en Odoo base.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Contacts",
    "license": "LGPL-3",
    "depends": ["base"],
    "installable": True,
    "application": False,
}
