from odoo import _, api, fields, models


class CosittMassEditEnabledModel(models.Model):
    _name = "cositt.mass.edit.enabled.model"
    _description = "Modelo habilitado para edición masiva (Cositt)"

    model_id = fields.Many2one("ir.model", string="Modelo", required=True, ondelete="cascade")
    model_name = fields.Char(related="model_id.model", store=True, readonly=True)
    # ir.actions.server creada/borrada junto con este registro: es lo que
    # realmente engancha "Edición masiva" al menú Acción de ese modelo.
    binding_action_id = fields.Many2one(
        "ir.actions.server", readonly=True, copy=False, ondelete="cascade"
    )

    _model_uniq = models.Constraint(
        "unique(model_id)", "Este modelo ya está habilitado para edición masiva."
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._cositt_sync_binding_action()
        return records

    def unlink(self):
        actions = self.binding_action_id
        result = super().unlink()
        actions.unlink()
        return result

    def _cositt_sync_binding_action(self):
        self.ensure_one()
        if self.binding_action_id:
            return
        action = self.env["ir.actions.server"].create({
            "name": _("Edición masiva"),
            "model_id": self.model_id.id,
            "binding_model_id": self.model_id.id,
            "binding_view_types": "list",
            "state": "code",
            "code": "action = env['cositt.mass.edit.wizard']._cositt_open_wizard(records)",
        })
        self.binding_action_id = action.id
