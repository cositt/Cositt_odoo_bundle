from odoo import _, models
from odoo.exceptions import UserError


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def cositt_action_open_postpone_wizard(self):
        # Entry point genérico enganchado a mail.activity (no a cada
        # modelo de negocio): funciona igual para actividades de
        # cualquier registro (factura, contacto, tarea...). Sin sudo():
        # si el usuario no tiene acceso a una de las actividades
        # seleccionadas, el propio ORM lo bloqueará al leer/escribir.
        if not self:
            raise UserError(_("Selecciona al menos una actividad para posponer."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Posponer actividades"),
            "res_model": "cositt.activity.postpone.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_activity_ids": [(6, 0, self.ids)]},
        }
