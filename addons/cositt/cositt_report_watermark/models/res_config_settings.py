from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cositt_watermark_enabled = fields.Boolean(
        related="company_id.cositt_watermark_enabled", readonly=False
    )
    cositt_watermark_text = fields.Char(
        related="company_id.cositt_watermark_text", readonly=False
    )
    cositt_watermark_opacity = fields.Integer(
        related="company_id.cositt_watermark_opacity", readonly=False
    )
    cositt_watermark_rotation = fields.Integer(
        related="company_id.cositt_watermark_rotation", readonly=False
    )

    def action_cositt_reset_watermark(self):
        self.ensure_one()
        self.company_id.action_cositt_reset_watermark()
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }
