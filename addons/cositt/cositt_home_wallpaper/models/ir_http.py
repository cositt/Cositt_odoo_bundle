from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        # Se inyecta en el HTML inicial (odoo.__session_info__, leído
        # síncronamente por web/static/src/session.js antes del primer
        # render) para que el Home Menu pueda pintar el fondo en el
        # primer patch, sin ninguna llamada RPC adicional ni parpadeo.
        # Mismo mecanismo que ya usa el propio Odoo para user_settings o
        # currencies en este mismo método (base web/models/ir_http.py).
        #
        # Sin sudo: res.company tiene lectura abierta a todos los
        # usuarios (incluido group_public) en el ACL base de Odoo — ya
        # es así antes de este módulo, no se amplía nada. Solo la
        # ESCRITURA de estos campos está restringida a Administración
        # (group_erp_manager), heredado también del propio res.company.
        info = super().session_info()
        info["cositt_home_wallpaper"] = self.env.company._cositt_get_wallpaper_config()
        return info
