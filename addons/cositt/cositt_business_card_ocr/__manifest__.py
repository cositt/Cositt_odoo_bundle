{
    "name": "Cositt Business Card OCR",
    "version": "19.0.1.0.0",
    "summary": "Escanea tarjetas de visita y crea contactos automáticamente",
    "description": """
Escanea una foto de tarjeta de visita, extrae los datos por OCR local
(Tesseract, sin enviar la imagen a ningún servicio externo) y permite
revisarlos antes de crear un contacto o añadirlo a una empresa existente.
Detecta posibles duplicados por email o teléfono antes de confirmar.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Sales/CRM",
    "license": "LGPL-3",
    "depends": ["contacts"],
    "external_dependencies": {
        "python": ["pytesseract", "PIL"],
        "bin": ["tesseract"],
    },
    "data": [
        "security/ir.model.access.csv",
        "security/cositt_card_scan_security.xml",
        "views/cositt_card_scan_views.xml",
    ],
    "installable": True,
    "application": False,
}
