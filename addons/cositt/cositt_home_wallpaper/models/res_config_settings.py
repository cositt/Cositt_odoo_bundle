from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # related + readonly=False: patrón estándar de Odoo para exponer
    # campos de res.company en Ajustes Generales (el propio
    # res.config.settings ya trae company_id apuntando a la compañía
    # activa) — sin necesidad de get_values()/set_values() manuales.
    cositt_wallpaper_enabled = fields.Boolean(
        related="company_id.cositt_wallpaper_enabled", readonly=False
    )
    cositt_wallpaper_image = fields.Image(
        related="company_id.cositt_wallpaper_image", readonly=False
    )
    cositt_wallpaper_color = fields.Char(
        related="company_id.cositt_wallpaper_color", readonly=False
    )
    cositt_wallpaper_overlay = fields.Integer(
        related="company_id.cositt_wallpaper_overlay", readonly=False
    )
    cositt_wallpaper_blur = fields.Integer(
        related="company_id.cositt_wallpaper_blur", readonly=False
    )
    cositt_wallpaper_fit = fields.Selection(
        related="company_id.cositt_wallpaper_fit", readonly=False
    )
    cositt_wallpaper_position = fields.Selection(
        related="company_id.cositt_wallpaper_position", readonly=False
    )

    def action_cositt_reset_wallpaper(self):
        self.ensure_one()
        self.company_id.action_cositt_reset_wallpaper()
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }
