from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        # Mismo mecanismo que cositt_backend_accent/cositt_kanban_ribbon_theme:
        # se inyecta en el HTML inicial (odoo.__session_info__), leído
        # síncronamente antes del primer render — cero RPC adicional. Sin
        # sudo: res.company ya es legible por cualquier usuario interno
        # de fábrica.
        info = super().session_info()
        config = self.env.company._cositt_get_announcement_banner_config()
        if config:
            info["cositt_announcement_banner"] = config
        return info
