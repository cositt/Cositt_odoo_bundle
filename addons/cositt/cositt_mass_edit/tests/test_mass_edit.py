from pathlib import Path

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Date, Datetime
from odoo.tests.common import TransactionCase


class TestCosittMassEdit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a = cls.env["res.partner"].create({"name": "Cliente A"})
        cls.partner_b = cls.env["res.partner"].create({"name": "Cliente B"})
        cls.company = cls.env["res.partner"].create(
            {"name": "Empresa Test", "is_company": True}
        )

    def _field(self, res_model, name):
        return self.env["ir.model.fields"].search(
            [("model", "=", res_model), ("name", "=", name)], limit=1
        )

    def _make_wizard(self, records, field_name, **vals):
        field_rec = self._field(records._name, field_name)
        self.assertTrue(field_rec, "campo %s no encontrado" % field_name)
        return self.env["cositt.mass.edit.wizard"].with_context(
            active_model=records._name, active_ids=records.ids,
        ).create({
            "res_model": records._name,
            "record_count": len(records),
            "allowed_field_ids": [(6, 0, [field_rec.id])],
            "field_id": field_rec.id,
            **vals,
        })

    # --- datos cargados ---------------------------------------------------

    def test_module_data_loaded(self):
        enabled = self.env.ref(
            "cositt_mass_edit.cositt_mass_edit_enabled_res_partner"
        )
        self.assertEqual(enabled.model_name, "res.partner")
        self.assertTrue(enabled.binding_action_id)
        self.assertEqual(enabled.binding_action_id.binding_model_id.model, "res.partner")
        self.assertEqual(enabled.binding_action_id.binding_view_types, "list")

    def test_enabling_model_creates_binding_action(self):
        model = self.env["ir.model"]._get("res.partner.category")
        enabled = self.env["cositt.mass.edit.enabled.model"].create(
            {"model_id": model.id}
        )
        self.assertTrue(enabled.binding_action_id)
        action = enabled.binding_action_id
        self.assertEqual(action.binding_model_id.model, "res.partner.category")

    def test_disabling_model_removes_binding_action(self):
        model = self.env["ir.model"]._get("res.partner.category")
        enabled = self.env["cositt.mass.edit.enabled.model"].create(
            {"model_id": model.id}
        )
        action = enabled.binding_action_id
        enabled.unlink()
        self.assertFalse(action.exists())

    # --- lista blanca de campos --------------------------------------------

    def test_safe_field_ids_excludes_technical_and_unsafe_fields(self):
        wizard_model = self.env["cositt.mass.edit.wizard"]
        safe_ids = wizard_model._cositt_get_safe_field_ids("res.partner")
        safe_names = set(
            self.env["ir.model.fields"].browse(safe_ids).mapped("name")
        )
        self.assertIn("name", safe_names)
        self.assertIn("function", safe_names)
        self.assertIn("is_company", safe_names)
        self.assertIn("parent_id", safe_names)
        for excluded in (
            "id", "create_date", "create_uid", "write_date", "write_uid",
            "category_id",  # many2many
            "child_ids",  # one2many
            "image_1920",  # binary
        ):
            self.assertNotIn(excluded, safe_names, "%s no debería ser editable" % excluded)

    def test_open_wizard_requires_records(self):
        with self.assertRaises(UserError):
            self.env["cositt.mass.edit.wizard"]._cositt_open_wizard(
                self.env["res.partner"]
            )

    def test_open_wizard_populates_allowed_fields(self):
        action = self.env["cositt.mass.edit.wizard"]._cositt_open_wizard(
            self.partner_a | self.partner_b
        )
        wizard = self.env["cositt.mass.edit.wizard"].browse(action["res_id"])
        self.assertEqual(wizard.record_count, 2)
        self.assertIn("name", wizard.allowed_field_ids.mapped("name"))

    def test_field_not_in_allowlist_is_blocked(self):
        other_field = self._field("res.partner", "function")
        wizard = self._make_wizard(self.partner_a, "name")
        with self.assertRaises(ValidationError):
            wizard.write({
                "allowed_field_ids": [(6, 0, [other_field.id])],
            })

    # --- aplicar por tipo ---------------------------------------------------

    def test_apply_char_field(self):
        wizard = self._make_wizard(
            self.partner_a | self.partner_b, "function", value_char="Director"
        )
        wizard.action_apply()
        self.assertEqual(self.partner_a.function, "Director")
        self.assertEqual(self.partner_b.function, "Director")

    def test_apply_boolean_field(self):
        wizard = self._make_wizard(
            self.partner_a | self.partner_b, "is_company", value_boolean=True
        )
        wizard.action_apply()
        self.assertTrue(self.partner_a.is_company)
        self.assertTrue(self.partner_b.is_company)

    def test_apply_selection_field(self):
        wizard = self._make_wizard(
            self.partner_a | self.partner_b, "type", value_selection="delivery"
        )
        wizard.action_apply()
        self.assertEqual(self.partner_a.type, "delivery")
        self.assertEqual(self.partner_b.type, "delivery")

    def test_apply_many2one_field(self):
        wizard = self._make_wizard(
            self.partner_a | self.partner_b, "parent_id",
            value_many2one_id=self.company.id,
        )
        wizard.action_apply()
        self.assertEqual(self.partner_a.parent_id, self.company)
        self.assertEqual(self.partner_b.parent_id, self.company)

    def test_dispatch_value_for_text_integer_float_date_datetime(self):
        # Estos tipos no tienen un campo real, seguro y ya editable de
        # serie en res.partner (p.ej. "comment" es Html, no Text, en esta
        # versión) — se prueba el despachador _cositt_get_write_value()
        # de forma aislada, apuntando a metadatos de campos ya existentes
        # en el propio core (sin necesidad de escribir de verdad).
        cases = [
            ("ir.model.fields", "help", "value_text", "Ayuda de prueba"),
            ("ir.sequence", "padding", "value_integer", 7),
            ("res.currency", "rounding", "value_float", 0.05),
            ("res.currency.rate", "name", "value_date", Date.today()),
            ("res.partner", "write_date", "value_datetime", Datetime.now().replace(microsecond=0)),
        ]
        for model_name, field_name, value_field, value in cases:
            field_rec = self._field(model_name, field_name)
            self.assertTrue(field_rec, "campo %s.%s no encontrado" % (model_name, field_name))
            wizard = self.env["cositt.mass.edit.wizard"].create({
                "res_model": model_name,
                "record_count": 1,
                "allowed_field_ids": [(6, 0, [field_rec.id])],
                "field_id": field_rec.id,
            })
            wizard.write({value_field: value})
            self.assertEqual(wizard._cositt_get_write_value(), value)

    def test_clear_field_on_optional_field(self):
        self.partner_a.function = "Director"
        wizard = self._make_wizard(self.partner_a, "function", clear_field=True)
        wizard.action_apply()
        self.assertFalse(self.partner_a.function)

    def test_clear_field_blocked_for_required_field(self):
        # res.partner.name no sirve para este caso: no es required=True a
        # nivel ORM (se exige vía un CHECK de base de datos, no vía
        # `required=True` de Python) — se usa un modelo con un campo
        # genuinamente required=True en el propio campo.
        category = self.env["res.partner.category"].create({"name": "Categoría X"})
        wizard = self._make_wizard(category, "name", clear_field=True)
        with self.assertRaises(UserError):
            wizard.action_apply()
        self.assertEqual(category.name, "Categoría X")

    # --- transacción atómica -------------------------------------------------

    def test_write_is_all_or_nothing_on_partial_denial(self):
        # Regla que bloquea SOLO partner_b: si el write no es atómico,
        # partner_a podría quedar cambiado y partner_b no (estado
        # incoherente). records.write() de una sola vez evita justamente
        # eso.
        restricted_group = self.env["res.groups"].create(
            {"name": "Cositt Mass Edit - grupo restringido (test)"}
        )
        self.env["ir.rule"].create({
            "name": "Bloqueo de un solo registro (test)",
            "model_id": self.env["ir.model"]._get("res.partner").id,
            "groups": [(6, 0, [restricted_group.id])],
            "domain_force": "[('id', '!=', %d)]" % self.partner_b.id,
        })
        restricted_admin = self.env.ref("base.user_admin")
        restricted_admin.group_ids = [(4, restricted_group.id)]

        wizard = self._make_wizard(
            self.partner_a | self.partner_b, "function", value_char="Director"
        )
        with self.assertRaises(AccessError):
            wizard.with_user(restricted_admin).action_apply()

        self.partner_a.invalidate_recordset()
        self.partner_b.invalidate_recordset()
        self.assertNotEqual(self.partner_a.function, "Director")
        self.assertNotEqual(self.partner_b.function, "Director")

    def test_respects_record_rules_without_sudo(self):
        restricted_group = self.env["res.groups"].create(
            {"name": "Cositt Mass Edit - grupo restringido total (test)"}
        )
        self.env["ir.rule"].create({
            "name": "Bloqueo total de prueba",
            "model_id": self.env["ir.model"]._get("res.partner").id,
            "groups": [(6, 0, [restricted_group.id])],
            "domain_force": "[('id', '=', False)]",
        })
        restricted_admin = self.env.ref("base.user_admin")
        restricted_admin.group_ids = [(4, restricted_group.id)]

        wizard = self._make_wizard(self.partner_a, "function", value_char="Director")
        with self.assertRaises(AccessError):
            wizard.with_user(restricted_admin).action_apply()

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
