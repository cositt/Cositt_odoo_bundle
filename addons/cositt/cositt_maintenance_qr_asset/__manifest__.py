{
    "name": "Cositt Maintenance QR Asset",
    "version": "19.0.1.0.0",
    "summary": "Genera un código QR de identificación para cada activo de Mantenimiento",
    "description": """
Añade un código QR en la ficha de cada activo de Mantenimiento, generado
localmente a partir de sus propios datos (nombre, categoría, modelo, nº de
serie, propietario, técnico asignado, garantía). Al escanearlo con la
cámara de un móvil se lee la ficha del activo directamente como texto,
sin necesitar conexión ni sesión abierta en Odoo — pensado para
etiquetas físicas pegadas al equipo.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Manufacturing/Maintenance",
    "license": "LGPL-3",
    "depends": ["maintenance"],
    "external_dependencies": {
        "python": ["qrcode"],
    },
    "data": [
        "views/maintenance_equipment_views.xml",
    ],
    "installable": True,
    "application": False,
}
