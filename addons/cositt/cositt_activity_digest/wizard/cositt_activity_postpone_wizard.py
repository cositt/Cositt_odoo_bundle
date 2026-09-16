from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CosittActivityPostponeWizard(models.TransientModel):
    _name = "cositt.activity.postpone.wizard"
    _description = "Posponer actividades"

    activity_ids = fields.Many2many("mail.activity", string="Actividades")
    activity_count = fields.Integer(compute="_compute_activity_count")
    days = fields.Integer(
        string="Días",
        default=1,
        required=True,
        help=(
            "Número de días que se suman a la fecha límite de cada "
            "actividad seleccionada. Usa un número negativo para "
            "adelantarla en vez de posponerla."
        ),
    )

    @api.depends("activity_ids")
    def _compute_activity_count(self):
        for wizard in self:
            wizard.activity_count = len(wizard.activity_ids)

    def action_postpone(self):
        self.ensure_one()
        if not self.activity_ids:
            raise UserError(_("No hay actividades seleccionadas."))
        if not self.days:
            raise UserError(_("Indica un número de días distinto de cero."))

        delta = timedelta(days=self.days)
        for activity in self.activity_ids:
            if activity.date_deadline:
                activity.date_deadline = activity.date_deadline + delta
