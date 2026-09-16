{
    "name": "Cositt Mass Edit",
    "version": "19.0.1.0.0",
    "summary": "Edición masiva controlada de un campo en varios registros seleccionados",
    "description": """
Selecciona varios registros en una vista de lista y cambia un campo en
todos a la vez (o vacíalo), sin tocar cada uno a mano. Solo funciona
sobre campos seguros (se excluyen técnicos, computados, relacionados,
de solo lectura y many2many/one2many/binary) y solo sobre los modelos
que el administrador habilite explícitamente desde Ajustes > Técnico.
Respeta permisos y record rules igual que una edición manual: si no
podrías cambiar un registro a mano, tampoco podrás con este asistente.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/cositt_mass_edit_enabled_model_views.xml",
        "views/cositt_mass_edit_wizard_views.xml",
        "data/cositt_mass_edit_enabled_model_data.xml",
    ],
    "installable": True,
    "application": False,
}
