from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# MVP a propósito: se deja fuera many2many/one2many (semántica ambigua —
# ¿reemplaza, añade o quita? — no lo simplifica una edición masiva
# genérica) y binary/html (contenido no apto para un input simple).
ALLOWED_FIELD_TYPES = {
    "char", "text", "integer", "float", "boolean",
    "selection", "many2one", "date", "datetime",
}
EXCLUDED_FIELD_NAMES = {
    "id", "create_uid", "create_date", "write_uid", "write_date",
    "__last_update", "display_name",
}


class CosittMassEditWizard(models.TransientModel):
    _name = "cositt.mass.edit.wizard"
    _description = "Edición masiva (Cositt)"

    res_model = fields.Char(required=True, readonly=True)
    record_count = fields.Integer(readonly=True)
    # Lista blanca calculada al abrir el asistente: el dominio de field_id
    # en la vista es solo UX, la seguridad real está en el @api.constrains
    # y en la comprobación repetida dentro de action_apply().
    allowed_field_ids = fields.Many2many("ir.model.fields", readonly=True)

    # Sin required=True a nivel Python: el asistente se crea SIN campo
    # elegido (lo elige el usuario después); la validación de "hace
    # falta un campo" vive en action_apply(), no aquí.
    field_id = fields.Many2one(
        "ir.model.fields", string="Campo",
        domain="[('id', 'in', allowed_field_ids)]",
    )
    field_type = fields.Selection(related="field_id.ttype", readonly=True)
    field_required = fields.Boolean(related="field_id.required", readonly=True)
    clear_field = fields.Boolean(string="Vaciar campo")

    # string= distinto por campo (evita el warning de "misma etiqueta" del
    # propio core); en la vista se muestran todos como "Valor" ya que solo
    # uno está visible a la vez según field_type.
    value_char = fields.Char(string="Valor (texto corto)")
    value_text = fields.Text(string="Valor (texto largo)")
    value_integer = fields.Integer(string="Valor (entero)")
    value_float = fields.Float(string="Valor (decimal)")
    value_boolean = fields.Boolean(string="Valor (sí/no)")
    value_selection = fields.Selection(
        selection="_selection_value_selection", string="Valor (opción)"
    )
    value_date = fields.Date(string="Valor (fecha)")
    value_datetime = fields.Datetime(string="Valor (fecha y hora)")
    # Many2oneReference (entero + nombre de modelo en un campo aparte) en
    # vez de Reference: Reference valida su "selection" dinámica vía
    # get_values(env) —a nivel de entorno, no de registro—, así que no
    # puede depender de field_id (un valor de ESTE MISMO registro). El
    # widget many2one_reference sí soporta un modelo "de otro campo"
    # (option model_field) resuelto por registro, que es justo lo que
    # hace falta aquí.
    value_many2one_model = fields.Char(compute="_compute_value_many2one_model")
    value_many2one_id = fields.Many2oneReference(
        string="Valor (relación)", model_field="value_many2one_model"
    )

    def _selection_value_selection(self):
        if self.field_id and self.field_id.ttype == "selection":
            real_field = self.env[self.field_id.model]._fields.get(self.field_id.name)
            if real_field is not None and isinstance(real_field.selection, list):
                return real_field.selection
        return []

    @api.depends("field_id")
    def _compute_value_many2one_model(self):
        for wizard in self:
            wizard.value_many2one_model = (
                wizard.field_id.relation
                if wizard.field_id and wizard.field_id.ttype == "many2one"
                else False
            )

    @api.constrains("field_id", "allowed_field_ids")
    def _check_field_is_allowed(self):
        for wizard in self:
            if wizard.field_id and wizard.field_id not in wizard.allowed_field_ids:
                raise ValidationError(
                    _("Este campo no está permitido para edición masiva.")
                )

    # --- apertura del asistente ------------------------------------------

    @api.model
    def _cositt_open_wizard(self, records):
        # Sin sudo(): "records" llega ya filtrado por los permisos del
        # usuario que ejecutó la acción (search/record rules estándar).
        if not records:
            raise UserError(_("Selecciona al menos un registro."))

        res_model = records._name
        allowed_ids = self._cositt_get_safe_field_ids(res_model)
        if not allowed_ids:
            raise UserError(
                _("No hay ningún campo editable de forma masiva en este modelo.")
            )

        wizard = self.create({
            "res_model": res_model,
            "record_count": len(records),
            "allowed_field_ids": [(6, 0, allowed_ids)],
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Edición masiva"),
            "res_model": "cositt.mass.edit.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
            "context": {"active_ids": records.ids, "active_model": res_model},
        }

    @api.model
    def _cositt_get_safe_field_ids(self, res_model):
        model = self.env[res_model]
        # fields_get() ya filtra por acceso del usuario actual (incluidos
        # los campos con groups= restringido): si no aparece aquí, el
        # usuario no debería ni verlo, mucho menos editarlo en lote.
        visible_field_names = model.fields_get(attributes=[])
        safe_names = []
        for name, field in model._fields.items():
            if name not in visible_field_names:
                continue
            if name in EXCLUDED_FIELD_NAMES:
                continue
            if field.type not in ALLOWED_FIELD_TYPES:
                continue
            if field.compute:
                continue
            if field.related:
                continue
            if field.readonly:
                continue
            if not field.store:
                continue
            safe_names.append(name)
        if not safe_names:
            return []
        return self.env["ir.model.fields"].search([
            ("model", "=", res_model), ("name", "in", safe_names),
        ]).ids

    # --- aplicar -----------------------------------------------------------

    def action_apply(self):
        self.ensure_one()
        if not self.field_id:
            raise UserError(_("Selecciona un campo."))
        if self.field_id not in self.allowed_field_ids:
            # Defensa en profundidad: el dominio de la vista es solo UX,
            # esto es lo que de verdad impide editar un campo no permitido
            # (p.ej. vía una llamada RPC directa saltándose la vista).
            raise UserError(_("Este campo no está permitido para edición masiva."))
        if self.clear_field and self.field_id.required:
            raise UserError(
                _('El campo "%s" es obligatorio: no se puede vaciar.')
                % self.field_id.field_description
            )

        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids") or []
        if active_model != self.res_model:
            raise UserError(
                _("Los registros seleccionados no coinciden con el modelo del asistente.")
            )
        if not active_ids:
            raise UserError(_("No hay registros seleccionados."))

        records = self.env[self.res_model].browse(active_ids)
        value = self._cositt_get_write_value()
        # Una sola llamada write() sobre todo el recordset: atómica de
        # serie (si un registro falla por permisos o restricción, no se
        # aplica ninguno), sin necesitar lógica de rollback propia.
        records.write({self.field_id.name: value})

        return {"type": "ir.actions.act_window_close"}

    def _cositt_get_write_value(self):
        if self.clear_field:
            return False
        ttype = self.field_id.ttype
        if ttype == "char":
            return self.value_char or False
        if ttype == "text":
            return self.value_text or False
        if ttype == "integer":
            return self.value_integer
        if ttype == "float":
            return self.value_float
        if ttype == "boolean":
            return self.value_boolean
        if ttype == "selection":
            return self.value_selection or False
        if ttype == "date":
            return self.value_date
        if ttype == "datetime":
            return self.value_datetime
        if ttype == "many2one":
            return self.value_many2one_id or False
        raise UserError(_("Tipo de campo no soportado."))
