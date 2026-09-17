from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        # Mismo mecanismo que cositt_home_wallpaper/cositt_login_background/
        # cositt_kanban_ribbon_theme: se inyecta en el HTML inicial
        # (odoo.__session_info__), leído síncronamente antes del primer
        # render — cero RPC adicional. Sin sudo: res.company ya es
        # legible por cualquier usuario interno de fábrica.
        info = super().session_info()
        color = self.env.company._cositt_get_backend_accent_color()
        if color:
            info["cositt_backend_accent_color"] = color
        return info
