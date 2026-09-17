from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Command
from odoo.tests import HttpCase, tagged
from odoo.tests.common import TransactionCase


class TestCosittKanbanRibbonRule(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Rule = cls.env["cositt.kanban.ribbon.rule"]
        # res.partner.category: modelo de base (siempre instalado), con
        # un campo Integer `color` real usado por su propio selector de
        # color nativo — no hace falta crear un modelo de prueba aparte.
        cls.category_model = cls.env.ref("base.model_res_partner_category")

    def _make_ordinary_user(self):
        user = self.env.ref("base.public_user")
        user.group_ids = [
            Command.unlink(self.env.ref("base.group_public").id),
            Command.link(self.env.ref("base.group_user").id),
        ]
        return user

    # --- valores por defecto: cero impacto sin configurar -------------

    def test_no_rules_means_no_ribbon_config(self):
        # Recordset vacío explícito, no search([]): esta base de dev
        # puede tener otras reglas de sesiones/verificaciones manuales
        # anteriores — search([]) devolvería esas también y el test
        # dependería de que el entorno estuviera "limpio" (hallazgo
        # real de code review: 5/14 tests fallaban así contra este
        # mismo cositt_plugins_dev).
        self.assertFalse(self.Rule.browse()._cositt_get_active_ribbon_rules())

    # --- reglas válidas -----------------------------------------------

    def test_valid_rule_appears_in_active_rules_dict(self):
        rule = self.Rule.create({
            "model_id": self.category_model.id,
            "color_field_name": "color",
        })
        # Sobre el recordset propio de la regla creada, no search([]) —
        # mismo motivo que arriba: aislado de cualquier otra regla que
        # ya exista en la base.
        self.assertEqual(
            rule._cositt_get_active_ribbon_rules(),
            {"res.partner.category": "color"},
        )

    def test_color_field_name_defaults_to_color(self):
        rule = self.Rule.create({"model_id": self.category_model.id})
        self.assertEqual(rule.color_field_name, "color")

    def test_model_name_is_denormalized_from_model_id(self):
        # Regresión directa del bug real de code review: session_info()
        # debe poder leer el modelo técnico sin volver a atravesar
        # model_id.model (eso dispara ACL sobre ir.model, que
        # base.group_user no puede leer — ver help de model_name).
        rule = self.Rule.create({"model_id": self.category_model.id})
        self.assertEqual(rule.model_name, "res.partner.category")

    def test_archived_rule_excluded_from_active_rules(self):
        rule = self.Rule.create({
            "model_id": self.category_model.id,
            "active": False,
        })
        self.assertEqual(rule._cositt_get_active_ribbon_rules(), {})

    # --- validaciones ----------------------------------------------------

    def test_nonexistent_field_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.Rule.create({
                "model_id": self.category_model.id,
                "color_field_name": "no_existe_este_campo",
            })

    def test_non_integer_field_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.Rule.create({
                "model_id": self.category_model.id,
                "color_field_name": "name",  # Char, no Integer
            })

    # --- unicidad por modelo (mismo patrón que cositt_smart_attachment_name) ---

    def test_duplicate_active_rule_for_same_model_is_rejected(self):
        self.Rule.create({"model_id": self.category_model.id})
        with self.assertRaises(ValidationError):
            self.Rule.create({"model_id": self.category_model.id})

    def test_can_create_new_rule_when_previous_one_is_archived(self):
        first = self.Rule.create({"model_id": self.category_model.id})
        first.active = False
        second = self.Rule.create({"model_id": self.category_model.id})
        self.assertTrue(second.active)

    # --- permisos: cualquier usuario interno puede leer, solo admin escribe ---

    def test_ordinary_user_can_read_rules(self):
        self.Rule.create({"model_id": self.category_model.id})
        user = self._make_ordinary_user()
        rules = self.Rule.with_user(user).search([])
        self.assertTrue(rules)

    def test_ordinary_user_can_compute_active_rules_without_access_error(self):
        # Regresión directa del HIGH real de code review: un usuario
        # interno normal (sin acceso a ir.model) NO debe reventar al
        # ejecutar exactamente lo que session_info() ejecuta en cada
        # carga del backend (ver models/ir_http.py). Antes del fix
        # (model_id.model en vez de model_name denormalizado), esto
        # lanzaba AccessError sobre ir.model — tumbando /odoo entero
        # para cualquier usuario no-administrador en cuanto existiera
        # una regla activa.
        rule = self.Rule.create({"model_id": self.category_model.id})
        user = self._make_ordinary_user()
        rules = self.Rule.with_user(user).browse(rule.ids)
        self.assertEqual(
            rules._cositt_get_active_ribbon_rules(),
            {"res.partner.category": "color"},
        )

    def test_ordinary_user_cannot_write_rules(self):
        rule = self.Rule.create({"model_id": self.category_model.id})
        user = self._make_ordinary_user()
        with self.assertRaises(AccessError):
            rule.with_user(user).write({"color_field_name": "color"})

    def test_ordinary_user_cannot_create_rules(self):
        user = self._make_ordinary_user()
        with self.assertRaises(AccessError):
            self.Rule.with_user(user).create({"model_id": self.category_model.id})

    # --- código -------------------------------------------------------------

    def test_module_never_calls_sudo(self):
        from pathlib import Path

        module_dir = Path(__file__).resolve().parent.parent
        for path in (module_dir / "models").glob("*.py"):
            self.assertNotIn(
                ".sudo(", path.read_text(encoding="utf-8"),
                "%s no debería usar sudo()" % path.name,
            )


@tagged("post_install", "-at_install")
class TestCosittKanbanRibbonHttp(HttpCase):
    """La lista de reglas activas viaja en session_info() — verificar
    contra el HTML real del webclient, no solo la función Python
    aislada (lección de cositt_login_background: un error de wiring
    entre el modelo y la plantilla no lo detecta un test unitario)."""

    def test_backend_session_info_reflects_configured_rule(self):
        # Antes/después en vez de asumir "{}" por defecto: esta base de
        # dev puede tener otras reglas de sesiones anteriores (hallazgo
        # real de code review — no asumir un entorno limpio).
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('"res.partner.category": "color"', response.text)

        category_model = self.env.ref("base.model_res_partner_category")
        self.env["cositt.kanban.ribbon.rule"].create({
            "model_id": category_model.id,
        })
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        self.assertIn('"res.partner.category": "color"', response.text)

    def test_backend_session_info_does_not_500_for_ordinary_user(self):
        # Regresión HTTP real del HIGH de code review (ver también
        # test_ordinary_user_can_compute_active_rules_without_access_error
        # más arriba, la misma cosa pero a nivel de request real): con
        # una regla activa, un usuario interno normal debía poder
        # cargar /odoo sin 500.
        category_model = self.env.ref("base.model_res_partner_category")
        self.env["cositt.kanban.ribbon.rule"].create({
            "model_id": category_model.id,
        })
        # Usuario interno real y activo, no base.public_user (ese es
        # un usuario técnico inactivo por diseño — self.authenticate()
        # hace un login real, no una impersonación a nivel ORM).
        from odoo.fields import Command
        user = self.env["res.users"].create({
            "name": "QA Kanban Ribbon",
            "login": "qa_kanban_ribbon",
            "password": "cositt_qa_1234",
            "group_ids": [Command.link(self.env.ref("base.group_user").id)],
        })
        self.authenticate(user.login, "cositt_qa_1234")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
