from odoo import api, fields, models


class CosittListColumnPreference(models.Model):
    _name = "cositt.list.column.preference"
    _description = "Preferencia de columnas opcionales de una lista (por usuario)"
    _rec_name = "view_key"

    user_id = fields.Many2one(
        "res.users", required=True, ondelete="cascade", index=True,
        default=lambda self: self.env.user,
    )
    # Mismo identificador que ya construye el propio Odoo en el cliente
    # (ListRenderer.createViewKey): modelo + vista + campo relacional (si
    # es una lista anidada, ej. un one2many) + lista de campos, así que
    # ya es único por vista/contexto sin que este módulo tenga que
    # inventar su propio esquema de claves.
    view_key = fields.Char(required=True)
    # CSV de nombres de campo activos, mismo formato que ya usa
    # localStorage en el cliente (ver static/src/list_renderer): así el
    # servidor no tiene que parsear/reconstruir nada distinto de lo que
    # el propio Odoo ya genera y consume.
    active_fields = fields.Char(required=True)

    _user_view_key_uniq = models.Constraint(
        "unique(user_id, view_key)",
        "Ya existe una preferencia de columnas guardada para esta vista y usuario.",
    )

    @api.model
    def cositt_get_active_fields(self, view_key):
        if not view_key:
            return False
        record = self.search([
            ("user_id", "=", self.env.uid), ("view_key", "=", view_key),
        ], limit=1)
        return record.active_fields if record else False

    @api.model
    def cositt_set_active_fields(self, view_key, active_fields):
        if not view_key:
            return False
        record = self.search([
            ("user_id", "=", self.env.uid), ("view_key", "=", view_key),
        ], limit=1)
        if record:
            record.active_fields = active_fields
        else:
            self.create({"view_key": view_key, "active_fields": active_fields})
        return True
