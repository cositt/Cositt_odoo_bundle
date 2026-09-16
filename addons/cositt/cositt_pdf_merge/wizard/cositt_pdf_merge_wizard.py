import base64
import io

from odoo import _, fields, models
from odoo.exceptions import UserError


class CosittPdfMergeWizard(models.TransientModel):
    _name = "cositt.pdf.merge.wizard"
    _description = "Combinar PDF"

    res_model = fields.Char(required=True, readonly=True)
    res_id = fields.Integer(required=True, readonly=True)
    line_ids = fields.One2many(
        "cositt.pdf.merge.wizard.line", "wizard_id", string="Documentos"
    )
    result_filename = fields.Char(string="Nombre del archivo", required=True)
    attach_to_record = fields.Boolean(
        string="Guardar como adjunto del registro",
        default=True,
        help=(
            "Además de poder descargarlo desde este asistente, guarda el PDF "
            "combinado como un nuevo adjunto de este registro."
        ),
    )
    # attachment=False: se guarda como columna normal de este wizard
    # temporal, no como un ir.attachment aparte que habría que limpiar.
    result_pdf = fields.Binary(string="PDF combinado", readonly=True, attachment=False)
    state = fields.Selection(
        [("select", "Seleccionar"), ("done", "Generado")],
        default="select",
        required=True,
    )

    def action_generate_pdf(self):
        self.ensure_one()
        lines = self.line_ids.filtered("selected").sorted("sequence")
        if not lines:
            raise UserError(_("Selecciona al menos un PDF para combinar."))
        if not (self.result_filename or "").strip():
            raise UserError(_("Indica un nombre para el archivo resultante."))

        attachment_model = self.env["ir.attachment"]
        streams = []
        stream_names = {}
        for line in lines:
            attachment = line.attachment_id
            if not attachment_model._cositt_is_pdf(attachment):
                raise UserError(
                    _('El adjunto "%s" no es un PDF y no se puede combinar.')
                    % attachment.name
                )
            raw = attachment.raw
            if not raw:
                raise UserError(
                    _('El adjunto "%s" está vacío y no se puede combinar.')
                    % attachment.name
                )
            stream = io.BytesIO(raw)
            streams.append(stream)
            stream_names[stream] = attachment.name

        corrupted = []

        def _handle_merge_error(error=None, error_stream=None):
            corrupted.append(stream_names[error_stream])

        merged_stream = self.env["ir.actions.report"]._merge_pdfs(
            streams, handle_error=_handle_merge_error
        )
        try:
            if corrupted:
                raise UserError(
                    _("No se pudo leer el siguiente PDF, puede estar dañado: %s")
                    % ", ".join(corrupted)
                )
            pdf_content = merged_stream.getvalue()
        finally:
            merged_stream.close()

        filename = self._cositt_ensure_pdf_extension(self.result_filename.strip())
        self.write({
            "result_pdf": base64.b64encode(pdf_content),
            "result_filename": filename,
            "state": "done",
        })

        if self.attach_to_record and self.res_model and self.res_id:
            attachment_model.create({
                "name": filename,
                "datas": self.result_pdf,
                "res_model": self.res_model,
                "res_id": self.res_id,
                "mimetype": "application/pdf",
            })

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @staticmethod
    def _cositt_ensure_pdf_extension(filename):
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        return filename


class CosittPdfMergeWizardLine(models.TransientModel):
    _name = "cositt.pdf.merge.wizard.line"
    _description = "Línea de combinación de PDF"
    _order = "sequence, id"

    wizard_id = fields.Many2one(
        "cositt.pdf.merge.wizard", required=True, ondelete="cascade"
    )
    attachment_id = fields.Many2one("ir.attachment", required=True, ondelete="cascade")
    name = fields.Char(related="attachment_id.name", string="Archivo", readonly=True)
    sequence = fields.Integer(default=10, string="Orden")
    selected = fields.Boolean(default=True, string="Incluir")
