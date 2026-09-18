from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cositt_announcement_banner_enabled = fields.Boolean(
        related="company_id.cositt_announcement_banner_enabled", readonly=False
    )
    cositt_announcement_banner_message = fields.Char(
        related="company_id.cositt_announcement_banner_message", readonly=False
    )
    cositt_announcement_banner_style = fields.Selection(
        related="company_id.cositt_announcement_banner_style", readonly=False
    )
