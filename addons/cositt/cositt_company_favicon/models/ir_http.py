from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        # Solo el título viaja por session_info() — el favicon es
        # puro server-side (link tag en <head>, ver
        # views/webclient_templates.xml), no necesita JS. El título SÍ
        # lo necesita para el backend: es una SPA que recalcula
        # document.title en cada navegación (ver
        # static/src/company_favicon/company_favicon.js), así que el
        # <title> server-side por sí solo no sobrevive más allá de la
        # carga inicial. Sin sudo: res.company ya es legible por
        # cualquier usuario interno de fábrica.
        info = super().session_info()
        title = self.env.company._cositt_get_browser_title()
        if title:
            info["cositt_browser_title"] = title
        return info
