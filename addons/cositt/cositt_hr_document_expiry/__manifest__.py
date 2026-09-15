{
    "name": "Cositt HR Document Expiry",
    "version": "19.0.1.0.0",
    "summary": "Avisa antes de que caduque un documento de un empleado (DNI, permiso de trabajo...)",
    "description": """
Añade una lista de documentos con fecha de caducidad en la ficha de cada
empleado (DNI/NIE, permiso de trabajo, carné de conducir, o cualquier
otro que se necesite). Un cron diario crea una actividad de recordatorio
antes de que caduque, asignada al propio empleado o a su responsable si
no tiene usuario, sin duplicar avisos ya abiertos.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Human Resources",
    "license": "LGPL-3",
    "depends": ["hr", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee_views.xml",
        "data/ir_cron.xml",
    ],
    "installable": True,
    "application": False,
}
