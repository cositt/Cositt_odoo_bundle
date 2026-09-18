from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cositt_seasonal_theme_enabled = fields.Boolean(
        related="company_id.cositt_seasonal_theme_enabled", readonly=False
    )
    cositt_seasonal_theme_kind = fields.Selection(
        related="company_id.cositt_seasonal_theme_kind", readonly=False
    )
    cositt_seasonal_theme_label = fields.Char(
        related="company_id.cositt_seasonal_theme_label", readonly=False
    )
    cositt_seasonal_theme_animation_enabled = fields.Boolean(
        related="company_id.cositt_seasonal_theme_animation_enabled", readonly=False
    )
    cositt_seasonal_theme_date_start = fields.Date(
        related="company_id.cositt_seasonal_theme_date_start", readonly=False
    )
    cositt_seasonal_theme_date_end = fields.Date(
        related="company_id.cositt_seasonal_theme_date_end", readonly=False
    )
