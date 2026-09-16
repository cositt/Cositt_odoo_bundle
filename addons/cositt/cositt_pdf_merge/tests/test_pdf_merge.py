import base64
import io
from pathlib import Path

from reportlab.pdfgen import canvas

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase
from odoo.tools.pdf import PdfFileReader


def _make_pdf_bytes(text):
    # PDF real y válido (no bytes a mano): así los tests de fusión/orden
    # ejercitan el mismo parser (PyPDF2, vía ir.actions.report._merge_pdfs)
    # que usa el módulo en producción, en vez de confiar en la
    # implementación interna.
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(200, 200))
    pdf.drawString(50, 100, text)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


class TestCosittPdfMerge(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Cliente de Prueba"})

    def _create_pdf_attachment(self, name, text, record=None):
        record = record or self.partner
        return self.env["ir.attachment"].create({
            "name": name,
            "res_model": record._name,
            "res_id": record.id,
            "mimetype": "application/pdf",
            "datas": base64.b64encode(_make_pdf_bytes(text)),
        })

    # --- instalación / datos cargados ---------------------------------

    def test_module_data_loaded(self):
        action = self.env.ref("cositt_pdf_merge.action_cositt_pdf_merge_wizard")
        self.assertEqual(action.model_id.model, "ir.attachment")
        access = self.env.ref("cositt_pdf_merge.access_cositt_pdf_merge_wizard_user")
        self.assertTrue(access.perm_create)

    # --- apertura del wizard: filtra solo PDF, exige selección --------

    def test_open_wizard_only_lists_pdf_attachments(self):
        pdf_a = self._create_pdf_attachment("a.pdf", "PAGE_A")
        self._create_pdf_attachment("b.pdf", "PAGE_B")
        self.env["ir.attachment"].create({
            "name": "foto.jpg",
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "mimetype": "image/jpeg",
            "datas": base64.b64encode(b"no es un pdf"),
        })

        action = pdf_a.cositt_action_open_pdf_merge_wizard()
        wizard = self.env["cositt.pdf.merge.wizard"].browse(action["res_id"])

        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(set(wizard.line_ids.mapped("name")), {"a.pdf", "b.pdf"})

    def test_open_wizard_requires_selection(self):
        with self.assertRaises(UserError):
            self.env["ir.attachment"].cositt_action_open_pdf_merge_wizard()

    def test_open_wizard_rejects_attachments_from_different_records(self):
        other_partner = self.env["res.partner"].create({"name": "Otro Cliente"})
        att_1 = self._create_pdf_attachment("a.pdf", "PAGE_A")
        att_2 = self._create_pdf_attachment("b.pdf", "PAGE_B", record=other_partner)
        with self.assertRaises(UserError):
            (att_1 | att_2).cositt_action_open_pdf_merge_wizard()

    def test_open_wizard_requires_at_least_one_pdf_on_record(self):
        record = self.env["res.partner"].create({"name": "Sin PDFs"})
        attachment = self.env["ir.attachment"].create({
            "name": "notas.txt",
            "res_model": "res.partner",
            "res_id": record.id,
            "mimetype": "text/plain",
            "datas": base64.b64encode(b"solo texto"),
        })
        with self.assertRaises(UserError):
            attachment.cositt_action_open_pdf_merge_wizard()

    # --- combinación: orden, contenido, adjunto resultante -------------

    def test_merge_two_valid_pdfs_respects_chosen_order(self):
        att_a = self._create_pdf_attachment("presupuesto.pdf", "PAGE_A")
        att_b = self._create_pdf_attachment("condiciones.pdf", "PAGE_B")
        wizard = self.env["cositt.pdf.merge.wizard"].create({
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "result_filename": "combinado",
            "line_ids": [
                # orden invertido a propósito respecto a la creación,
                # para comprobar que manda "sequence", no el orden de alta.
                (0, 0, {"attachment_id": att_b.id, "sequence": 10}),
                (0, 0, {"attachment_id": att_a.id, "sequence": 20}),
            ],
        })

        wizard.action_generate_pdf()

        self.assertEqual(wizard.state, "done")
        self.assertEqual(wizard.result_filename, "combinado.pdf")
        merged_bytes = base64.b64decode(wizard.result_pdf)
        reader = PdfFileReader(io.BytesIO(merged_bytes))
        self.assertEqual(reader.getNumPages(), 2)
        self.assertIn("PAGE_B", reader.getPage(0).extract_text())
        self.assertIn("PAGE_A", reader.getPage(1).extract_text())

    def test_generate_creates_attachment_on_record_when_requested(self):
        att_a = self._create_pdf_attachment("a.pdf", "PAGE_A")
        att_b = self._create_pdf_attachment("b.pdf", "PAGE_B")
        before = self.env["ir.attachment"].search_count([
            ("res_model", "=", "res.partner"), ("res_id", "=", self.partner.id),
        ])
        wizard = self.env["cositt.pdf.merge.wizard"].create({
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "result_filename": "documentacion_completa",
            "attach_to_record": True,
            "line_ids": [
                (0, 0, {"attachment_id": att_a.id, "sequence": 10}),
                (0, 0, {"attachment_id": att_b.id, "sequence": 20}),
            ],
        })

        wizard.action_generate_pdf()

        after = self.env["ir.attachment"].search([
            ("res_model", "=", "res.partner"), ("res_id", "=", self.partner.id),
        ])
        self.assertEqual(len(after), before + 1)
        new_attachment = after.filtered(
            lambda a: a.name == "documentacion_completa.pdf"
        )
        self.assertEqual(len(new_attachment), 1)
        self.assertEqual(new_attachment.mimetype, "application/pdf")

    def test_generate_does_not_create_attachment_when_not_requested(self):
        att_a = self._create_pdf_attachment("a.pdf", "PAGE_A")
        att_b = self._create_pdf_attachment("b.pdf", "PAGE_B")
        before = self.env["ir.attachment"].search_count([
            ("res_model", "=", "res.partner"), ("res_id", "=", self.partner.id),
        ])
        wizard = self.env["cositt.pdf.merge.wizard"].create({
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "result_filename": "combinado",
            "attach_to_record": False,
            "line_ids": [
                (0, 0, {"attachment_id": att_a.id, "sequence": 10}),
                (0, 0, {"attachment_id": att_b.id, "sequence": 20}),
            ],
        })

        wizard.action_generate_pdf()

        after_count = self.env["ir.attachment"].search_count([
            ("res_model", "=", "res.partner"), ("res_id", "=", self.partner.id),
        ])
        self.assertEqual(after_count, before)

    # --- validaciones ---------------------------------------------------

    def test_generate_without_selected_lines_raises(self):
        att_a = self._create_pdf_attachment("a.pdf", "PAGE_A")
        wizard = self.env["cositt.pdf.merge.wizard"].create({
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "result_filename": "combinado",
            "line_ids": [
                (0, 0, {
                    "attachment_id": att_a.id, "sequence": 10, "selected": False,
                }),
            ],
        })
        with self.assertRaises(UserError):
            wizard.action_generate_pdf()

    def test_generate_rejects_non_pdf_line(self):
        # Defensa en profundidad: aunque la vista solo ofrece PDFs, la
        # validación en Python también rechaza un adjunto no-PDF si llegara
        # a colarse una línea (RPC directo, manipulación de datos...).
        bad_attachment = self.env["ir.attachment"].create({
            "name": "no_es_pdf.txt",
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "mimetype": "text/plain",
            "datas": base64.b64encode(b"contenido de texto"),
        })
        wizard = self.env["cositt.pdf.merge.wizard"].create({
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "result_filename": "combinado",
            "line_ids": [
                (0, 0, {"attachment_id": bad_attachment.id, "sequence": 10}),
            ],
        })
        with self.assertRaises(UserError):
            wizard.action_generate_pdf()

    def test_generate_with_empty_attachment_raises_clear_message(self):
        empty_attachment = self.env["ir.attachment"].create({
            "name": "vacio.pdf",
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "mimetype": "application/pdf",
            "datas": base64.b64encode(b""),
        })
        wizard = self.env["cositt.pdf.merge.wizard"].create({
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "result_filename": "combinado",
            "line_ids": [
                (0, 0, {"attachment_id": empty_attachment.id, "sequence": 10}),
            ],
        })
        with self.assertRaises(UserError) as capture:
            wizard.action_generate_pdf()
        self.assertIn("vacio.pdf", str(capture.exception))

    def test_generate_with_corrupted_pdf_raises_clear_message(self):
        corrupted_attachment = self.env["ir.attachment"].create({
            "name": "danado.pdf",
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "mimetype": "application/pdf",
            "datas": base64.b64encode(b"%PDF-1.4 esto no es un pdf valido"),
        })
        wizard = self.env["cositt.pdf.merge.wizard"].create({
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "result_filename": "combinado",
            "line_ids": [
                (0, 0, {"attachment_id": corrupted_attachment.id, "sequence": 10}),
            ],
        })
        with self.assertRaises(UserError) as capture:
            wizard.action_generate_pdf()
        self.assertIn("danado.pdf", str(capture.exception))

    def test_generate_requires_result_filename(self):
        att_a = self._create_pdf_attachment("a.pdf", "PAGE_A")
        wizard = self.env["cositt.pdf.merge.wizard"].create({
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "result_filename": "   ",
            "line_ids": [(0, 0, {"attachment_id": att_a.id, "sequence": 10})],
        })
        with self.assertRaises(UserError):
            wizard.action_generate_pdf()

    # --- permisos: sin sudo, respeta record rules -----------------------

    def test_respects_record_rules_without_sudo(self):
        # No hay dependencia de hr/sale/account en este módulo, así que la
        # restricción se simula con un ir.rule temporal sobre res.partner.
        # Se usa base.public_user (usuario ya existente del propio core,
        # sin privilegios) en vez de crear un res.users nuevo: en este
        # entorno, res.users.create() fallaba bajo --test-enable por un
        # problema de entorno ajeno a este módulo, y además el usuario de
        # la propia sesión de test resulta ser el superusuario real
        # (bypassa ir.rule por definición, no serviría para este test).
        restricted_group = self.env["res.groups"].create(
            {"name": "Cositt PDF Merge - grupo restringido (test)"}
        )
        self.env["ir.rule"].create({
            "name": "Bloqueo total de prueba",
            "model_id": self.env["ir.model"]._get("res.partner").id,
            "groups": [(6, 0, [restricted_group.id])],
            "domain_force": "[('id', '=', False)]",
        })
        attachment = self._create_pdf_attachment("confidencial.pdf", "PAGE_A")
        public_user = self.env.ref("base.public_user")
        public_user.group_ids = [(4, restricted_group.id)]

        with self.assertRaises(AccessError):
            attachment.with_user(public_user).cositt_action_open_pdf_merge_wizard()

    def test_module_never_calls_sudo(self):
        # Complementa el test anterior: comprobación directa (no solo de
        # comportamiento) de que el código de este módulo no usa sudo() en
        # ningún punto, tal y como exige la especificación de seguridad.
        module_dir = Path(__file__).resolve().parent.parent
        python_files = [
            *(module_dir / "models").glob("*.py"),
            *(module_dir / "wizard").glob("*.py"),
        ]
        self.assertTrue(python_files)
        for path in python_files:
            self.assertNotIn(
                ".sudo(", path.read_text(encoding="utf-8"),
                "%s no debería usar sudo()" % path.name,
            )
