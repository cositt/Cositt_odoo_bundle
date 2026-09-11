{
    "name": "Cositt Duplicate Contacts",
    "version": "19.0.1.0.0",
    "summary": "Detecta contactos duplicados por teléfono y facilita fusionarlos",
    "description": """
Odoo ya incluye un asistente de fusión de contactos (reasigna facturas,
mensajes y actividades de forma segura), pero está oculto y no agrupa por
teléfono. Este módulo añade esa opción y un acceso directo desde Contactos
para detectar y fusionar duplicados de forma controlada.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Contacts",
    "license": "LGPL-3",
    # phone_validation aporta el campo phone_sanitized que usamos en SQL
    # crudo (_generate_query). No declararlo permitiría desinstalarlo sin
    # aviso y rompería la consulta con un error de columna inexistente.
    "depends": ["contacts", "phone_validation"],
    "data": [
        "views/base_partner_merge_views.xml",
    ],
    "installable": True,
    "application": False,
}
