import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


def _is_low_stock(qty_available, low_stock_threshold):
    """Función pura: un umbral <= 0 significa "desactivado" para ese
    producto, nunca dispara aviso."""
    if low_stock_threshold <= 0:
        return False
    return qty_available <= low_stock_threshold


class ProductTemplate(models.Model):
    _inherit = "product.template"

    low_stock_threshold = fields.Float(
        default=0,
        help="Cantidad disponible a partir de la cual se avisa de stock "
        "bajo. 0 desactiva el aviso para este producto. En productos con "
        "variantes, se compara contra el stock combinado de todas ellas, "
        "no de una variante concreta.",
    )
    is_low_stock = fields.Boolean(compute="_compute_is_low_stock")

    @api.depends("qty_available", "low_stock_threshold")
    def _compute_is_low_stock(self):
        for product in self:
            product.is_low_stock = _is_low_stock(
                product.qty_available, product.low_stock_threshold
            )

    @api.model
    def _cron_check_low_stock(self):
        # low_stock_threshold es un campo real y almacenado, así que el
        # domain de búsqueda es barato; qty_available es dinámico (se
        # calcula al vuelo desde stock.quant en cada movimiento), así que
        # comparar contra el umbral (otro campo del mismo registro) se
        # hace en Python sobre ese conjunto ya acotado, no sobre todo el
        # catálogo.
        candidates = self.search([("low_stock_threshold", ">", 0)])
        alert_activity_type = self.env.ref(
            "cositt_stock_low_alert.mail_activity_type_low_stock_alert"
        )
        for product in candidates:
            # responsible_id es company_dependent; un cron corre con el
            # contexto de UNA sola compañía (la del usuario del ir.cron).
            # Para un producto con company_id propio, forzamos ese
            # contexto explícitamente en vez de dejarlo al azar del
            # usuario del cron. Un producto sin company_id (compartido
            # entre varias) queda fuera de este caso simple: se avisa
            # igual, pero con el "Responsible" de la compañía del cron,
            # que puede no ser el correcto para todas — se deja constancia
            # en el log en vez de fallar en silencio.
            if not product.company_id:
                _logger.warning(
                    "Producto '%s' (id=%s) sin compañía asignada "
                    "(compartido entre compañías): el aviso de stock bajo "
                    "usará el 'Responsible' de la compañía por defecto del "
                    "cron, que puede no ser el correcto para todas.",
                    product.name,
                    product.id,
                )
            product = product.with_company(product.company_id or self.env.company)

            if not _is_low_stock(product.qty_available, product.low_stock_threshold):
                continue

            already_alerted = product.activity_ids.filtered(
                lambda a: a.activity_type_id == alert_activity_type
            )
            if already_alerted:
                continue

            if not product.responsible_id:
                _logger.warning(
                    "No se pudo avisar de stock bajo para '%s' (id=%s): "
                    "no tiene 'Responsible' asignado.",
                    product.name,
                    product.id,
                )
                continue

            try:
                with self.env.cr.savepoint():
                    product.activity_schedule(
                        activity_type_id=alert_activity_type.id,
                        summary=self.env._(
                            "Low stock: %(name)s (%(qty)s available, "
                            "threshold %(threshold)s)",
                            name=product.name,
                            qty=f"{product.qty_available:g}",
                            threshold=f"{product.low_stock_threshold:g}",
                        ),
                        user_id=product.responsible_id.id,
                    )
            except Exception:
                _logger.exception(
                    "No se pudo crear el aviso de stock bajo para '%s' (id=%s).",
                    product.name,
                    product.id,
                )
