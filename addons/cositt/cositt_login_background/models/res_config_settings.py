from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cositt_login_bg_enabled = fields.Boolean(
        related="company_id.cositt_login_bg_enabled", readonly=False
    )
    cositt_login_bg_image = fields.Image(
        related="company_id.cositt_login_bg_image", readonly=False
    )
    cositt_login_bg_color = fields.Char(
        related="company_id.cositt_login_bg_color", readonly=False
    )
    cositt_login_bg_overlay = fields.Integer(
        related="company_id.cositt_login_bg_overlay", readonly=False
    )
    cositt_login_bg_blur = fields.Integer(
        related="company_id.cositt_login_bg_blur", readonly=False
    )
    cositt_login_bg_fit = fields.Selection(
        related="company_id.cositt_login_bg_fit", readonly=False
    )
    cositt_login_bg_position = fields.Selection(
        related="company_id.cositt_login_bg_position", readonly=False
    )

    def action_cositt_reset_login_bg(self):
        self.ensure_one()
        self.company_id.action_cositt_reset_login_bg()
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }
