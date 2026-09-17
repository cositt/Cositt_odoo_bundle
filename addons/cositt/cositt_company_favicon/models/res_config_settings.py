from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cositt_branding_enabled = fields.Boolean(
        related="company_id.cositt_branding_enabled", readonly=False
    )
    cositt_favicon_image = fields.Image(
        related="company_id.cositt_favicon_image", readonly=False
    )
    cositt_browser_title = fields.Char(
        related="company_id.cositt_browser_title", readonly=False
    )
