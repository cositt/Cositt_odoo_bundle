import base64
import io
import zipfile

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CosittAttachmentZipWizard(models.TransientModel):
    _name = "cositt.attachment.zip.wizard"
    _description = "Descargar adjuntos (ZIP)"

    attachment_ids = fields.Many2many(
        "ir.attachment", string="Adjuntos seleccionados", readonly=True
    )
    attachment_count = fields.Integer(compute="_compute_summary")
    record_count = fields.Integer(compute="_compute_summary")
    total_size_display = fields.Char(compute="_compute_summary")
    zip_filename = fields.Char(string="Nombre del archivo", default="adjuntos.zip")
    # attachment=False: columna normal de este wizard temporal, no un
    # ir.attachment aparte que habría que limpiar (mismo criterio que
    # cositt_pdf_merge.result_pdf).
    zip_file = fields.Binary(string="Archivo ZIP", readonly=True, attachment=False)
    state = fields.Selection(
        [("select", "Seleccionar"), ("done", "Generado")],
        default="select",
        required=True,
    )

    @api.depends("attachment_ids")
    def _compute_summary(self):
        for wizard in self:
            attachments = wizard.attachment_ids
            wizard.attachment_count = len(attachments)
            wizard.record_count = len(attachments._cositt_group_by_record())
            total_size = sum(attachments.mapped("file_size"))
            wizard.total_size_display = attachments._cositt_human_size(total_size)

    def action_generate_zip(self):
        self.ensure_one()
        attachments = self.attachment_ids
        if not attachments:
            raise UserError(_("No hay adjuntos para descargar."))
        if not (self.zip_filename or "").strip():
            raise UserError(_("Indica un nombre para el archivo ZIP."))

        attachments._cositt_check_zip_limits()

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_archive:
            for (res_model, res_id), group in attachments._cositt_group_by_record().items():
                folder = group._cositt_folder_name_for(res_model, res_id)
                filenames = group._cositt_dedupe_names([
                    group._cositt_sanitize_path_component(a.name, _("sin_nombre"))
                    for a in group
                ])
                for attachment, filename in zip(group, filenames):
                    zip_archive.writestr(
                        "%s/%s" % (folder, filename), attachment.raw or b""
                    )
        zip_bytes = buffer.getvalue()

        filename = self._cositt_ensure_zip_extension(self.zip_filename.strip())
        self.write({
            "zip_file": base64.b64encode(zip_bytes),
            "zip_filename": filename,
            "state": "done",
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @staticmethod
    def _cositt_ensure_zip_extension(filename):
        if not filename.lower().endswith(".zip"):
            filename += ".zip"
        return filename
