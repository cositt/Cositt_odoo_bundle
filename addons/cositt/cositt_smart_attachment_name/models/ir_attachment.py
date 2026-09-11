import logging
import os
import re

from odoo import api, models

_logger = logging.getLogger(__name__)

TOKEN_RE = re.compile(r"\{([\w.]+)\}")
UNSAFE_CHARS_RE = re.compile(r'[\\/:*?"<>|\n\r\t]')
MAX_NAME_LENGTH = 150


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model_create_multi
    def create(self, vals_list):
        rules_by_model = self._cositt_get_naming_rules()
        if rules_by_model:
            for vals in vals_list:
                self._cositt_apply_naming_rule(vals, rules_by_model)
        return super().create(vals_list)

    @api.model
    def _cositt_get_naming_rules(self):
        # sudo(): la regla debe aplicarse para cualquier usuario que suba un
        # adjunto, no solo para quien tenga acceso a configurar las reglas.
        rules = self.env["cositt.attachment.naming.rule"].sudo().search(
            [("active", "=", True)]
        )
        return {rule.model_id.model: rule.pattern for rule in rules if rule.model_id}

    def _cositt_apply_naming_rule(self, vals, rules_by_model):
        # Una regla mal escrita (campo inexistente, etc.) nunca debe impedir
        # que el archivo se suba: se registra el problema y se sigue sin
        # renombrar, en vez de propagar la excepción.
        try:
            res_model = vals.get("res_model")
            res_id = vals.get("res_id")
            current_name = vals.get("name")
            if not (res_model and res_id and current_name):
                return
            pattern = rules_by_model.get(res_model)
            if not pattern or res_model not in self.env:
                return

            record = self.env[res_model].browse(res_id)
            if not record.exists():
                return

            new_base = self._cositt_render_pattern(pattern, record)
            if new_base:
                _, ext = os.path.splitext(current_name)
                vals["name"] = "%s%s" % (new_base, ext)
        except Exception:
            _logger.exception(
                "cositt_smart_attachment_name: no se pudo aplicar la regla de "
                "nombrado, se conserva el nombre original"
            )

    @api.model
    def _cositt_render_pattern(self, pattern, record):
        def _replace(match):
            field_path = match.group(1)
            try:
                values = record.mapped(field_path)
            except Exception:
                _logger.warning(
                    "cositt_smart_attachment_name: campo inválido '%s' en el "
                    "patrón para %s",
                    field_path,
                    record._name,
                )
                return ""
            value = values[0] if values else None
            if value is None or value is False or value == "":
                return ""
            if isinstance(value, models.BaseModel):
                # {partner_id} en vez de {partner_id.name}: usar
                # display_name en vez del repr interno del registro.
                value = value.display_name or ""
            return self._cositt_sanitize(str(value))

        rendered = TOKEN_RE.sub(_replace, pattern)
        rendered = self._cositt_sanitize(rendered).strip("_ ")
        return rendered or False

    @staticmethod
    def _cositt_sanitize(text):
        text = UNSAFE_CHARS_RE.sub("_", text)
        text = re.sub(r"\s+", "_", text.strip())
        return text[:MAX_NAME_LENGTH]
