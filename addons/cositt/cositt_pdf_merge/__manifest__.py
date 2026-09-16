{
    "name": "Cositt PDF Merge",
    "version": "19.0.1.0.0",
    "summary": "Combina varios PDF adjuntos a un registro en un único archivo",
    "description": """
Selecciona varios adjuntos PDF de un mismo registro (presupuesto, factura,
contacto, proyecto, tarea...) y genera un único PDF combinado, respetando el
orden elegido. Reutiliza el propio mecanismo de fusión de PDF de Odoo
(el mismo que usa el envío por lote de facturas/informes), sin añadir
ninguna dependencia externa nueva.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/cositt_pdf_merge_wizard_views.xml",
        "data/ir_actions_server.xml",
    ],
    "installable": True,
    "application": False,
}
