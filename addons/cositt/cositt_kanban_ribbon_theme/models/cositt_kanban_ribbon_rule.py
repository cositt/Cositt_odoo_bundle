from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CosittKanbanRibbonRule(models.Model):
    _name = "cositt.kanban.ribbon.rule"
    _description = "Regla de ribbon de color en tarjetas kanban"

    model_id = fields.Many2one(
        "ir.model",
        string="Modelo",
        required=True,
        ondelete="cascade",
        domain="[('transient', '=', False)]",
        help="Las tarjetas kanban de este modelo mostrarán un ribbon de "
        "color según el campo elegido abajo.",
    )
    model_name = fields.Char(
        string="Modelo técnico",
        related="model_id.model",
        store=True,
        help="Nombre técnico denormalizado (no una relación en vivo) a "
        "propósito: session_info() (ver models/ir_http.py) lo lee para "
        "CUALQUIER usuario interno, y leer model_id.model directamente "
        "ahí dispara una comprobación de ACL sobre ir.model, que "
        "base.group_user NO puede leer en el core de Odoo — bug real "
        "encontrado en code review: con una regla activa, session_info() "
        "reventaba con AccessError para todo usuario no-administrador, "
        "tumbando el backend entero para ellos (no solo el kanban). Al "
        "guardarlo como Char normal (aunque related+store, calculado una "
        "sola vez cuando escribe un admin), la lectura posterior pasa por "
        "el ACL de cositt.kanban.ribbon.rule, abierto a group_user — sin "
        "necesitar sudo().",
    )
    color_field_name = fields.Char(
        string="Campo de color",
        default="color",
        required=True,
        help='Nombre técnico de un campo Integer del modelo (por defecto '
        '"color", el mismo que ya usa el selector de color nativo de '
        "Odoo en la mayoría de modelos).",
    )
    active = fields.Boolean(default=True)

    @api.constrains("model_id", "color_field_name")
    def _check_color_field_exists_and_is_integer(self):
        for rule in self:
            if not rule.model_id or not rule.color_field_name:
                continue
            model = self.env.get(rule.model_id.model)
            field = model._fields.get(rule.color_field_name) if model is not None else None
            if field is None:
                raise ValidationError(_(
                    'El modelo "%(model)s" no tiene ningún campo llamado '
                    '"%(field)s".'
                ) % {"model": rule.model_id.model, "field": rule.color_field_name})
            if field.type != "integer":
                raise ValidationError(_(
                    'El campo "%(field)s" de "%(model)s" no es un campo '
                    "numérico (Integer) — no puede usarse como índice de "
                    "color."
                ) % {"field": rule.color_field_name, "model": rule.model_id.model})

    @api.constrains("model_id", "active")
    def _check_unique_active_rule_per_model(self):
        # Restricción en Python (no SQL) a propósito, mismo patrón que
        # cositt_smart_attachment_name: una restricción SQL
        # unique(model_id) bloquearía crear una regla nueva si la única
        # anterior para ese modelo está archivada.
        for rule in self:
            if not rule.active:
                continue
            duplicate = self.search([
                ("model_id", "=", rule.model_id.id),
                ("active", "=", True),
                ("id", "!=", rule.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    _("Ya existe una regla de ribbon activa para este modelo.")
                )

    def _cositt_get_active_ribbon_rules(self):
        """{modelo_técnico: nombre_de_campo} de las reglas activas —
        listo para inyectar en session_info() (ver models/ir_http.py).
        Se llama sobre un recordset ya filtrado por el propio caller
        (o sobre el modelo entero); solo se consideran las activas.

        Usa model_name (denormalizado), NUNCA model_id.model aquí: ver
        el help de model_name arriba para el bug real que esto evita."""
        return {
            rule.model_name: rule.color_field_name
            for rule in self
            if rule.active
        }
