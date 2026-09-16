{
    "name": "Cositt Attachment Zip",
    "version": "19.0.1.0.0",
    "summary": "Descarga en ZIP los adjuntos de uno o varios registros seleccionados",
    "description": """
Selecciona uno o varios adjuntos (de cualquier modelo: presupuesto, factura,
contacto, proyecto, tarea...) desde Ajustes > Técnico > Adjuntos y descarga
un único ZIP con una carpeta por registro de origen, sin nombres de archivo
duplicados dentro de cada carpeta. Enganchado directamente sobre
ir.attachment (no sobre modelos de negocio concretos): funciona igual para
cualquier modelo sin añadir dependencias funcionales. Respeta permisos y
record rules igual que una descarga manual (sin sudo): si no podrías leer
un adjunto a mano, tampoco aparece en el ZIP. Sin dependencias externas
(usa zipfile de la librería estándar de Python). Aplica un límite de
número de adjuntos y de tamaño total por descarga para evitar cargar
archivos gigantes en memoria sin aviso (ver README).
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/cositt_attachment_zip_wizard_views.xml",
        "data/ir_actions_server.xml",
    ],
    "installable": True,
    "application": False,
}
