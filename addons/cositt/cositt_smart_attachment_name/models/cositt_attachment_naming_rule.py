from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CosittAttachmentNamingRule(models.Model):
    _name = "cositt.attachment.naming.rule"
    _description = "Regla de nombrado automático de adjuntos"
    _order = "sequence, id"

    name = fields.Char(required=True, help="Solo para identificar la regla.")
    model_id = fields.Many2one(
        "ir.model",
        string="Modelo",
        required=True,
        ondelete="cascade",
        domain="[('transient', '=', False)]",
        help="Los adjuntos que se suban a registros de este modelo se renombrarán.",
    )
    pattern = fields.Char(
        required=True,
        string="Patrón de nombre",
        help=(
            'Usa {campo} o {campo.subcampo} para insertar datos del registro, '
            'p.ej. "Factura_{name}_{partner_id.name}". La extensión del '
            "archivo (.pdf, .jpg...) se conserva siempre."
        ),
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    @api.constrains("model_id", "active")
    def _check_unique_active_rule_per_model(self):
        # Restricción en Python (no SQL) a propósito: una restricción SQL
        # unique(model_id) bloquearía también a los modelos cuya única
        # regla está archivada (active=False), impidiendo crear una regla
        # nueva para ese modelo sin antes encontrar y reactivar/editar la
        # archivada. Aquí solo se exige unicidad entre reglas ACTIVAS.
        for rule in self:
            if not rule.active:
                continue
            duplicate = self.search(
                [
                    ("model_id", "=", rule.model_id.id),
                    ("active", "=", True),
                    ("id", "!=", rule.id),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(
                    _("Ya existe una regla de nombrado activa para este modelo.")
                )
