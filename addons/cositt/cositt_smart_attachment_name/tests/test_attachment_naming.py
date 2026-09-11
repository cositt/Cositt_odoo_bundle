import base64

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

FAKE_CONTENT = base64.b64encode(b"contenido de prueba").decode()


class TestAttachmentNaming(TransactionCase):
    def _model_id(self, model_name):
        return self.env["ir.model"]._get(model_name)

    def _create_attachment(self, res_model, res_id, name):
        return self.env["ir.attachment"].create(
            {
                "name": name,
                "res_model": res_model,
                "res_id": res_id,
                "datas": FAKE_CONTENT,
            }
        )

    def test_rule_unique_per_active_model(self):
        model_id = self._model_id("res.partner").id
        self.env["cositt.attachment.naming.rule"].create(
            {"name": "Regla 1", "model_id": model_id, "pattern": "{name}"}
        )
        with self.assertRaises(ValidationError):
            self.env["cositt.attachment.naming.rule"].create(
                {"name": "Regla 2", "model_id": model_id, "pattern": "Otra_{name}"}
            )

    def test_can_create_new_rule_after_archiving_old_one(self):
        # Regresión: una restricción SQL unique(model_id) bloquearía esto
        # aunque la regla anterior esté archivada. La unicidad solo debe
        # exigirse entre reglas activas.
        model_id = self._model_id("res.partner").id
        old_rule = self.env["cositt.attachment.naming.rule"].create(
            {"name": "Vieja", "model_id": model_id, "pattern": "{name}"}
        )
        old_rule.active = False

        new_rule = self.env["cositt.attachment.naming.rule"].create(
            {"name": "Nueva", "model_id": model_id, "pattern": "Nuevo_{name}"}
        )
        self.assertTrue(new_rule.active)

        # Reactivar la vieja mientras la nueva sigue activa sí debe fallar.
        with self.assertRaises(ValidationError):
            old_rule.active = True

    def test_renames_attachment_using_pattern(self):
        partner = self.env["res.partner"].create({"name": "ACME Corp"})
        self.env["cositt.attachment.naming.rule"].create(
            {
                "name": "Contactos",
                "model_id": self._model_id("res.partner").id,
                "pattern": "Contacto_{name}",
            }
        )

        attachment = self._create_attachment("res.partner", partner.id, "scan.pdf")
        self.assertEqual(attachment.name, "Contacto_ACME_Corp.pdf")

    def test_preserves_extension(self):
        partner = self.env["res.partner"].create({"name": "Foto Test"})
        self.env["cositt.attachment.naming.rule"].create(
            {
                "name": "Contactos",
                "model_id": self._model_id("res.partner").id,
                "pattern": "{name}",
            }
        )

        attachment = self._create_attachment("res.partner", partner.id, "photo.JPG")
        self.assertTrue(attachment.name.endswith(".JPG"))

    def test_no_matching_rule_leaves_name_unchanged(self):
        # No hay ninguna regla creada para res.company en este test.
        company = self.env.company
        attachment = self._create_attachment(
            "res.company", company.id, "documento.pdf"
        )
        self.assertEqual(attachment.name, "documento.pdf")

    def test_invalid_field_in_pattern_does_not_crash(self):
        partner = self.env["res.partner"].create({"name": "Test Campo Invalido"})
        self.env["cositt.attachment.naming.rule"].create(
            {
                "name": "Regla Rota",
                "model_id": self._model_id("res.partner").id,
                "pattern": "X_{campo_que_no_existe}_Y",
            }
        )

        attachment = self._create_attachment("res.partner", partner.id, "a.pdf")
        self.assertTrue(attachment.exists())
        self.assertIn("X_", attachment.name)
        self.assertIn("_Y.pdf", attachment.name)

    def test_empty_render_preserves_original_name(self):
        partner = self.env["res.partner"].create({"name": "Test Vacio"})
        self.env["cositt.attachment.naming.rule"].create(
            {
                "name": "Regla Vacia",
                "model_id": self._model_id("res.partner").id,
                "pattern": "{campo_que_no_existe}",
            }
        )

        attachment = self._create_attachment("res.partner", partner.id, "original.pdf")
        self.assertEqual(attachment.name, "original.pdf")

    def test_sanitizes_unsafe_characters(self):
        partner = self.env["res.partner"].create({"name": "A/B:C*D"})
        self.env["cositt.attachment.naming.rule"].create(
            {
                "name": "Contactos",
                "model_id": self._model_id("res.partner").id,
                "pattern": "{name}",
            }
        )

        attachment = self._create_attachment("res.partner", partner.id, "a.pdf")
        for unsafe in ("/", ":", "*"):
            self.assertNotIn(unsafe, attachment.name)

    def test_falsy_zero_value_is_not_treated_as_missing(self):
        # color es un Integer que por defecto vale 0: un 0 legítimo no debe
        # tratarse igual que un campo vacío/inexistente.
        partner = self.env["res.partner"].create({"name": "Color Cero", "color": 0})
        self.env["cositt.attachment.naming.rule"].create(
            {
                "name": "Contactos",
                "model_id": self._model_id("res.partner").id,
                "pattern": "Color_{color}",
            }
        )

        attachment = self._create_attachment("res.partner", partner.id, "a.pdf")
        self.assertEqual(attachment.name, "Color_0.pdf")

    def test_relational_field_without_subfield_uses_display_name(self):
        company = self.env["res.partner"].create(
            {"name": "Empresa Padre SL", "is_company": True}
        )
        partner = self.env["res.partner"].create(
            {"name": "Empleado", "parent_id": company.id}
        )
        self.env["cositt.attachment.naming.rule"].create(
            {
                "name": "Contactos",
                "model_id": self._model_id("res.partner").id,
                # {parent_id} sin subcampo: error típico de un usuario sin
                # conocimientos técnicos configurando la regla.
                "pattern": "{parent_id}",
            }
        )

        attachment = self._create_attachment("res.partner", partner.id, "a.pdf")
        self.assertIn("Empresa_Padre_SL", attachment.name)
        self.assertNotIn("res.partner(", attachment.name)

    def test_inactive_rule_is_ignored(self):
        partner = self.env["res.partner"].create({"name": "Regla Inactiva"})
        rule = self.env["cositt.attachment.naming.rule"].create(
            {
                "name": "Contactos",
                "model_id": self._model_id("res.partner").id,
                "pattern": "Contacto_{name}",
            }
        )
        rule.active = False

        attachment = self._create_attachment("res.partner", partner.id, "scan.pdf")
        self.assertEqual(attachment.name, "scan.pdf")

    def test_attachment_without_res_model_is_left_alone(self):
        attachment = self.env["ir.attachment"].create(
            {"name": "suelto.pdf", "datas": FAKE_CONTENT}
        )
        self.assertEqual(attachment.name, "suelto.pdf")

    def test_unknown_res_model_is_left_alone(self):
        # Defensivo: una regla normal siempre apunta a un ir.model real
        # (Many2one), pero _cositt_apply_naming_rule no debe romperse si
        # alguna vez recibe un res_model que no existe como modelo Odoo.
        vals = {"name": "a.pdf", "res_model": "no.existe.modelo", "res_id": 1}
        self.env["ir.attachment"]._cositt_apply_naming_rule(
            vals, {"no.existe.modelo": "{name}"}
        )
        self.assertEqual(vals["name"], "a.pdf")

    def test_batch_create_with_mixed_models_in_one_call(self):
        partner = self.env["res.partner"].create({"name": "Lote Uno"})
        company = self.env.company
        self.env["cositt.attachment.naming.rule"].create(
            {
                "name": "Contactos",
                "model_id": self._model_id("res.partner").id,
                "pattern": "Contacto_{name}",
            }
        )
        # No hay regla para res.company en este test.

        attachments = self.env["ir.attachment"].create(
            [
                {
                    "name": "scan1.pdf",
                    "res_model": "res.partner",
                    "res_id": partner.id,
                    "datas": FAKE_CONTENT,
                },
                {
                    "name": "scan2.pdf",
                    "res_model": "res.company",
                    "res_id": company.id,
                    "datas": FAKE_CONTENT,
                },
            ]
        )
        self.assertEqual(attachments[0].name, "Contacto_Lote_Uno.pdf")
        self.assertEqual(attachments[1].name, "scan2.pdf")
