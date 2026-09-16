{
    "name": "Cositt Activity Digest",
    "version": "19.0.1.0.0",
    "summary": "Menú \"Mis Actividades\" (todos los modelos) + posponer varias de una vez",
    "description": """
Odoo ya trae una vista completa de "Mis Actividades" (vencidas, de hoy, de
mañana...) que reúne las actividades programadas en cualquier modelo, pero
no la enlaza a ningún menú: solo la usa el propio widget del reloj y la
paleta de comandos (Ctrl+K). Este módulo la expone en un menú normal y
añade "Posponer": mover varias actividades seleccionadas un número
cualquiera de días (o negativo, para adelantarlas) de una vez — Odoo ya
trae accesos rápidos a Hoy/Mañana/Próxima semana en lote, pero no a un
número arbitrario de días.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/cositt_activity_digest_menus.xml",
        "views/cositt_activity_postpone_wizard_views.xml",
        "data/ir_actions_server.xml",
    ],
    "installable": True,
    "application": False,
}
