import re

from odoo import _, api, models
from odoo.exceptions import UserError

UNSAFE_CHARS_RE = re.compile(r'[\\/:*?"<>|\n\r\t]')
MAX_BASENAME_LENGTH = 100


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def cositt_action_open_pdf_merge_wizard(self):
        # Entry point bound generically to ir.attachment (Ajustes > Técnico >
        # Adjuntos): funciona igual para cualquier modelo (presupuesto,
        # factura, contacto, proyecto...) sin depender de sale/account/project
        # y sin tocar la vista de cada modelo. Se apoya solo en los permisos
        # normales de ir.attachment/el registro padre, sin sudo().
        if not self:
            raise UserError(_("Selecciona al menos un adjunto para combinar."))

        targets = {
            (attachment.res_model, attachment.res_id)
            for attachment in self
            if attachment.res_model and attachment.res_id
        }
        if not targets:
            raise UserError(
                _("Los adjuntos seleccionados no están vinculados a ningún registro.")
            )
        if len(targets) > 1:
            raise UserError(
                _("Selecciona adjuntos de un único registro: la selección "
                  "actual mezcla adjuntos de %d registros distintos.") % len(targets)
            )

        res_model, res_id = targets.pop()
        record = self.env[res_model].browse(res_id)
        if not record.exists():
            raise UserError(_("El registro asociado a estos adjuntos ya no existe."))

        pdf_attachments = self._cositt_search_pdf_attachments(res_model, res_id)
        if not pdf_attachments:
            raise UserError(_("Este registro no tiene ningún archivo PDF adjunto."))

        wizard = self.env["cositt.pdf.merge.wizard"].create({
            "res_model": res_model,
            "res_id": res_id,
            "result_filename": self._cositt_default_result_filename(record),
            "line_ids": [
                (0, 0, {"attachment_id": attachment.id, "sequence": index * 10})
                for index, attachment in enumerate(pdf_attachments, start=1)
            ],
        })

        return {
            "type": "ir.actions.act_window",
            "name": _("Combinar PDF"),
            "res_model": "cositt.pdf.merge.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def _cositt_search_pdf_attachments(self, res_model, res_id):
        return self.search([
            ("res_model", "=", res_model),
            ("res_id", "=", res_id),
            "|",
            ("mimetype", "=", "application/pdf"),
            ("name", "=ilike", "%.pdf"),
        ], order="id")

    @api.model
    def _cositt_is_pdf(self, attachment):
        return bool(attachment) and (
            attachment.mimetype == "application/pdf"
            or (attachment.name or "").lower().endswith(".pdf")
        )

    @api.model
    def _cositt_default_result_filename(self, record):
        base = (record.display_name or "documento").strip()
        base = re.sub(r"\s+", "_", base)
        base = UNSAFE_CHARS_RE.sub("_", base)[:MAX_BASENAME_LENGTH]
        return "%s_combinado.pdf" % (base or "documento")
