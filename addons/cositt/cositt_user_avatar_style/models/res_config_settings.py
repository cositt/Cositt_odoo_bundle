from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cositt_avatar_style_enabled = fields.Boolean(
        related="company_id.cositt_avatar_style_enabled", readonly=False
    )
    cositt_avatar_style_palette = fields.Char(
        related="company_id.cositt_avatar_style_palette", readonly=False
    )
