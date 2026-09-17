from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        # Mismo mecanismo que ya usan cositt_home_wallpaper y
        # cositt_login_background: se inyecta en el HTML inicial
        # (odoo.__session_info__), leído síncronamente antes del
        # primer render — cero RPC por vista kanban abierta.
        #
        # Sin sudo: la lectura de cositt.kanban.ribbon.rule está
        # abierta a cualquier usuario interno (ver
        # security/ir.model.access.csv) — necesario para que CUALQUIER
        # usuario que abra un kanban reciba la lista de modelos
        # configurados, no solo los administradores. Solo la
        # ESCRITURA está restringida a Administración/Ajustes
        # Técnicos.
        info = super().session_info()
        rules = self.env["cositt.kanban.ribbon.rule"].search([])
        info["cositt_kanban_ribbon_rules"] = rules._cositt_get_active_ribbon_rules()
        return info
