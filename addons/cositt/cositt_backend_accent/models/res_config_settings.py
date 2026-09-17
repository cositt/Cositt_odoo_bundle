from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cositt_backend_accent_enabled = fields.Boolean(
        related="company_id.cositt_backend_accent_enabled", readonly=False
    )
    cositt_backend_accent_color = fields.Char(
        related="company_id.cositt_backend_accent_color", readonly=False
    )
