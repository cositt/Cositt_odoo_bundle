{
    "name": "Cositt Stock Low Alert",
    "version": "19.0.1.0.0",
    "summary": "Avisa cuando el stock de un producto cruza un umbral mínimo configurable",
    "description": """
Añade un umbral de stock mínimo por producto. Un cron diario crea una
actividad de recordatorio, asignada al "Responsible" del producto (campo
nativo de Inventario), cuando el stock disponible cae a ese umbral o por
debajo. No requiere configurar reglas de reabastecimiento (ruta de
compra/fabricación, proveedor...): es un simple aviso, complementario a
esas reglas, no un sustituto.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Inventory",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "views/product_template_views.xml",
        "data/mail_activity_type.xml",
        "data/ir_cron.xml",
    ],
    "installable": True,
    "application": False,
}
