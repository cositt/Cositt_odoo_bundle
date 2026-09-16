import base64
import io
import zipfile
from pathlib import Path
from unittest import mock

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase

MODULE = "odoo.addons.cositt_attachment_zip.models.ir_attachment"


class TestCosittAttachmentZip(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Cliente de Prueba"})

    def _create_attachment(self, name, content, record=None, mimetype="text/plain"):
        record = record or self.partner
        return self.env["ir.attachment"].create({
            "name": name,
            "res_model": record._name,
            "res_id": record.id,
            "mimetype": mimetype,
            "datas": base64.b64encode(content),
        })

    def _open_zip(self, wizard):
        return zipfile.ZipFile(io.BytesIO(base64.b64decode(wizard.zip_file)))

    # --- instalación / datos cargados ---------------------------------

    def test_module_data_loaded(self):
        action = self.env.ref("cositt_attachment_zip.action_cositt_attachment_zip_wizard")
        self.assertEqual(action.model_id.model, "ir.attachment")
        access = self.env.ref(
            "cositt_attachment_zip.access_cositt_attachment_zip_wizard_user"
        )
        self.assertTrue(access.perm_create)

    # --- apertura del wizard --------------------------------------------

    def test_open_wizard_requires_selection(self):
        with self.assertRaises(UserError):
            self.env["ir.attachment"].cositt_action_open_attachment_zip_wizard()

    def test_open_wizard_creates_wizard_with_selected_attachments(self):
        att_a = self._create_attachment("a.txt", b"AAA")
        att_b = self._create_attachment("b.txt", b"BBB")

        action = (att_a | att_b).cositt_action_open_attachment_zip_wizard()
        wizard = self.env["cositt.attachment.zip.wizard"].browse(action["res_id"])

        self.assertEqual(wizard.state, "select")
        self.assertEqual(set(wizard.attachment_ids.ids), {att_a.id, att_b.id})
        self.assertEqual(wizard.attachment_count, 2)
        self.assertEqual(wizard.record_count, 1)

    # --- generación: agrupación por registro, dedup, contenido ---------

    def test_generate_zip_groups_attachments_by_record_in_separate_folders(self):
        other_partner = self.env["res.partner"].create({"name": "Otro Cliente"})
        att_a = self._create_attachment("a.txt", b"CONTENIDO_A")
        att_b = self._create_attachment("b.txt", b"CONTENIDO_B", record=other_partner)

        wizard = self.env["cositt.attachment.zip.wizard"].create({
            "attachment_ids": [(6, 0, [att_a.id, att_b.id])],
        })
        wizard.action_generate_zip()

        self.assertEqual(wizard.state, "done")
        with self._open_zip(wizard) as zf:
            names = set(zf.namelist())
            self.assertIn("Cliente de Prueba/a.txt", names)
            self.assertIn("Otro Cliente/b.txt", names)
            self.assertEqual(zf.read("Cliente de Prueba/a.txt"), b"CONTENIDO_A")
            self.assertEqual(zf.read("Otro Cliente/b.txt"), b"CONTENIDO_B")

    def test_generate_zip_dedupes_filenames_within_same_folder(self):
        att_a = self._create_attachment("factura.pdf", b"UNO")
        att_b = self._create_attachment("factura.pdf", b"DOS")

        wizard = self.env["cositt.attachment.zip.wizard"].create({
            "attachment_ids": [(6, 0, [att_a.id, att_b.id])],
        })
        wizard.action_generate_zip()

        with self._open_zip(wizard) as zf:
            names = set(zf.namelist())
            self.assertIn("Cliente de Prueba/factura.pdf", names)
            self.assertIn("Cliente de Prueba/factura_2.pdf", names)

    def test_generate_zip_handles_orphan_attachment_without_record(self):
        orphan = self.env["ir.attachment"].create({
            "name": "suelto.txt",
            "datas": base64.b64encode(b"HUERFANO"),
        })
        wizard = self.env["cositt.attachment.zip.wizard"].create({
            "attachment_ids": [(6, 0, [orphan.id])],
        })
        wizard.action_generate_zip()

        with self._open_zip(wizard) as zf:
            names = zf.namelist()
            self.assertEqual(len(names), 1)
            self.assertTrue(names[0].startswith("Sin registro vinculado/"))
            self.assertEqual(zf.read(names[0]), b"HUERFANO")

    def test_generate_zip_uses_chosen_filename_with_zip_extension(self):
        att_a = self._create_attachment("a.txt", b"AAA")
        wizard = self.env["cositt.attachment.zip.wizard"].create({
            "attachment_ids": [(6, 0, [att_a.id])],
            "zip_filename": "mi_descarga",
        })
        wizard.action_generate_zip()
        self.assertEqual(wizard.zip_filename, "mi_descarga.zip")

    # --- validaciones -----------------------------------------------------

    def test_generate_without_attachments_raises(self):
        wizard = self.env["cositt.attachment.zip.wizard"].create({})
        with self.assertRaises(UserError):
            wizard.action_generate_zip()

    def test_generate_requires_zip_filename(self):
        att_a = self._create_attachment("a.txt", b"AAA")
        wizard = self.env["cositt.attachment.zip.wizard"].create({
            "attachment_ids": [(6, 0, [att_a.id])],
            "zip_filename": "   ",
        })
        with self.assertRaises(UserError):
            wizard.action_generate_zip()

    def test_generate_zip_enforces_attachment_count_limit(self):
        att_a = self._create_attachment("a.txt", b"AAA")
        att_b = self._create_attachment("b.txt", b"BBB")
        wizard = self.env["cositt.attachment.zip.wizard"].create({
            "attachment_ids": [(6, 0, [att_a.id, att_b.id])],
        })
        with mock.patch(MODULE + ".MAX_ATTACHMENT_COUNT", 1):
            with self.assertRaises(UserError):
                wizard.action_generate_zip()

    def test_generate_zip_enforces_total_size_limit(self):
        att_a = self._create_attachment("a.txt", b"X" * 1000)
        wizard = self.env["cositt.attachment.zip.wizard"].create({
            "attachment_ids": [(6, 0, [att_a.id])],
        })
        with mock.patch(MODULE + ".MAX_TOTAL_SIZE_BYTES", 10):
            with self.assertRaises(UserError):
                wizard.action_generate_zip()

    # --- lógica pura: sanitizado / dedup, sin ORM -------------------------

    def test_sanitize_path_component_blocks_traversal(self):
        attachment_model = self.env["ir.attachment"]
        result = attachment_model._cositt_sanitize_path_component(
            "../../etc/passwd", "fallback"
        )
        self.assertNotIn("/", result)
        self.assertNotIn("\\", result)
        self.assertNotEqual(result, "..")

    def test_sanitize_path_component_falls_back_when_only_unsafe_chars(self):
        attachment_model = self.env["ir.attachment"]
        result = attachment_model._cositt_sanitize_path_component("....", "fallback")
        self.assertEqual(result, "fallback")

    def test_sanitize_path_component_strips_separators(self):
        attachment_model = self.env["ir.attachment"]
        result = attachment_model._cositt_sanitize_path_component(
            'a/b\\c:d*e?f"g<h>i|j', "fallback"
        )
        for char in '/\\:*?"<>|':
            self.assertNotIn(char, result)

    def test_dedupe_names_pure(self):
        attachment_model = self.env["ir.attachment"]
        result = attachment_model._cositt_dedupe_names(
            ["factura.pdf", "factura.pdf", "nota.txt", "factura.pdf"]
        )
        self.assertEqual(result, [
            "factura.pdf", "factura_2.pdf", "nota.txt", "factura_3.pdf",
        ])

    def test_dedupe_names_no_collision_leaves_names_unchanged(self):
        attachment_model = self.env["ir.attachment"]
        result = attachment_model._cositt_dedupe_names(["a.txt", "b.txt"])
        self.assertEqual(result, ["a.txt", "b.txt"])

    # --- permisos: sin sudo, respeta record rules -------------------------

    def test_respects_record_rules_without_sudo(self):
        # Mismo patrón que cositt_pdf_merge: base.public_user (existente,
        # sin privilegios) + ir.rule temporal, porque res.users.create()
        # falla bajo --test-enable en este entorno (ver memoria del
        # proyecto) y la sesión de test corre como superusuario real
        # (bypassa ir.rule por definición).
        restricted_group = self.env["res.groups"].create(
            {"name": "Cositt Attachment Zip - grupo restringido (test)"}
        )
        self.env["ir.rule"].create({
            "name": "Bloqueo total de prueba",
            "model_id": self.env["ir.model"]._get("res.partner").id,
            "groups": [(6, 0, [restricted_group.id])],
            "domain_force": "[('id', '=', False)]",
        })
        attachment = self._create_attachment("confidencial.txt", b"SECRETO")
        public_user = self.env.ref("base.public_user")
        public_user.group_ids = [(4, restricted_group.id)]

        with self.assertRaises(AccessError):
            attachment.with_user(public_user).cositt_action_open_attachment_zip_wizard()

    def test_module_never_calls_sudo(self):
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
