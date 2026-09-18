from datetime import timedelta

from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Command, Date
from odoo.tests import HttpCase, tagged
from odoo.tests.common import TransactionCase


class TestCosittSeasonalTheme(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def setUp(self):
        super().setUp()
        # No asumir compañía limpia: cositt_plugins_dev es una base
        # compartida con verificación manual entre sesiones (mismo
        # hallazgo que en cositt_kanban_ribbon_theme y
        # cositt_announcement_banner) — se fuerza un estado conocido.
        self.company.write({
            "cositt_seasonal_theme_enabled": False,
            "cositt_seasonal_theme_kind": "christmas",
            "cositt_seasonal_theme_label": False,
            "cositt_seasonal_theme_animation_enabled": True,
            "cositt_seasonal_theme_date_start": False,
            "cositt_seasonal_theme_date_end": False,
        })

    def _make_ordinary_user(self):
        user = self.env.ref("base.public_user")
        user.group_ids = [
            Command.unlink(self.env.ref("base.group_public").id),
            Command.link(self.env.ref("base.group_user").id),
        ]
        return user

    # --- valores por defecto: cero impacto sin configurar -------------

    def test_default_state_is_disabled(self):
        company = self.env["res.company"].create({"name": "QA Seasonal Co"})
        self.assertFalse(company.cositt_seasonal_theme_enabled)
        self.assertEqual(company.cositt_seasonal_theme_kind, "christmas")
        self.assertTrue(company.cositt_seasonal_theme_animation_enabled)

    def test_config_returns_false_when_disabled(self):
        self.assertFalse(self.company._cositt_get_seasonal_theme_config())

    def test_config_returns_dict_when_enabled_without_dates(self):
        self.company.cositt_seasonal_theme_enabled = True
        config = self.company._cositt_get_seasonal_theme_config()
        self.assertEqual(config["kind"], "christmas")
        self.assertFalse(config["label"])
        self.assertTrue(config["animation_enabled"])

    def test_config_includes_label_when_set(self):
        self.company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_label": "¡Feliz Navidad, equipo!",
        })
        config = self.company._cositt_get_seasonal_theme_config()
        self.assertEqual(config["label"], "¡Feliz Navidad, equipo!")

    def test_config_reflects_animation_toggle(self):
        self.company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_animation_enabled": False,
        })
        config = self.company._cositt_get_seasonal_theme_config()
        self.assertFalse(config["animation_enabled"])

    # --- rango de fechas -------------------------------------------------

    def test_config_false_before_start_date(self):
        self.company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_date_start": Date.today() + timedelta(days=5),
        })
        self.assertFalse(self.company._cositt_get_seasonal_theme_config())

    def test_config_false_after_end_date(self):
        self.company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_date_end": Date.today() - timedelta(days=1),
        })
        self.assertFalse(self.company._cositt_get_seasonal_theme_config())

    def test_config_true_within_date_range(self):
        self.company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_date_start": Date.today() - timedelta(days=1),
            "cositt_seasonal_theme_date_end": Date.today() + timedelta(days=1),
        })
        self.assertTrue(self.company._cositt_get_seasonal_theme_config())

    def test_config_true_with_only_start_date_in_past(self):
        self.company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_date_start": Date.today() - timedelta(days=30),
        })
        self.assertTrue(self.company._cositt_get_seasonal_theme_config())

    def test_config_true_with_only_end_date_in_future(self):
        self.company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_date_end": Date.today() + timedelta(days=30),
        })
        self.assertTrue(self.company._cositt_get_seasonal_theme_config())

    def test_config_true_exactly_on_start_date(self):
        self.company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_date_start": Date.today(),
        })
        self.assertTrue(self.company._cositt_get_seasonal_theme_config())

    def test_config_true_exactly_on_end_date(self):
        self.company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_date_end": Date.today(),
        })
        self.assertTrue(self.company._cositt_get_seasonal_theme_config())

    def test_end_date_before_start_date_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.write({
                "cositt_seasonal_theme_date_start": Date.today(),
                "cositt_seasonal_theme_date_end": Date.today() - timedelta(days=1),
            })

    def test_same_start_and_end_date_is_accepted(self):
        today = Date.today()
        self.company.write({
            "cositt_seasonal_theme_date_start": today,
            "cositt_seasonal_theme_date_end": today,
        })
        self.assertEqual(self.company.cositt_seasonal_theme_date_end, today)

    # --- validación del mensaje ------------------------------------------

    def test_label_over_max_length_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_seasonal_theme_label = "x" * 141

    def test_label_at_max_length_is_accepted(self):
        label = "x" * 140
        self.company.cositt_seasonal_theme_label = label
        self.assertEqual(self.company.cositt_seasonal_theme_label, label)

    # --- permisos: hereda el ACL/reglas ya existentes de res.company ---

    def test_ordinary_user_cannot_write_seasonal_theme_fields(self):
        user = self._make_ordinary_user()
        with self.assertRaises(AccessError):
            self.company.with_user(user).write({"cositt_seasonal_theme_enabled": True})

    def test_ordinary_user_can_read_seasonal_theme_fields(self):
        self.company.cositt_seasonal_theme_enabled = True
        user = self._make_ordinary_user()
        value = self.company.with_user(user).cositt_seasonal_theme_enabled
        self.assertTrue(value)

    # --- multiempresa --------------------------------------------------

    def test_each_company_has_independent_theme(self):
        other_company = self.env["res.company"].create({"name": "QA Seasonal Co 2"})
        self.company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_kind": "fair",
        })
        other_company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_kind": "birthday",
        })
        self.assertEqual(self.company._cositt_get_seasonal_theme_config()["kind"], "fair")
        self.assertEqual(other_company._cositt_get_seasonal_theme_config()["kind"], "birthday")

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
class TestCosittSeasonalThemeHttp(HttpCase):
    """El tema viaja en session_info() — verificar contra el HTML real de
    /odoo, no solo la función Python aislada (mismo criterio que
    cositt_announcement_banner/cositt_backend_accent)."""

    def setUp(self):
        super().setUp()
        # Mismo motivo que TestCosittSeasonalTheme.setUp(): cositt_plugins_dev
        # es una base compartida con verificación manual en navegador —
        # no asumir que la compañía real está limpia.
        self.env.company.write({
            "cositt_seasonal_theme_enabled": False,
            "cositt_seasonal_theme_kind": "christmas",
            "cositt_seasonal_theme_label": False,
            "cositt_seasonal_theme_animation_enabled": True,
            "cositt_seasonal_theme_date_start": False,
            "cositt_seasonal_theme_date_end": False,
        })

    def test_backend_session_info_omits_theme_by_default(self):
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("cositt_seasonal_theme", response.text)

    def test_backend_session_info_includes_theme_when_active(self):
        self.env.company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_kind": "fair",
        })
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        self.assertIn('"cositt_seasonal_theme"', response.text)
        self.assertIn('"kind": "fair"', response.text)

    def test_backend_session_info_omits_theme_outside_date_range(self):
        self.env.company.write({
            "cositt_seasonal_theme_enabled": True,
            "cositt_seasonal_theme_date_end": Date.today() - timedelta(days=1),
        })
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("cositt_seasonal_theme", response.text)

    def test_backend_loads_for_ordinary_user_when_active(self):
        self.env.company.write({"cositt_seasonal_theme_enabled": True})
        user = self.env["res.users"].create({
            "name": "QA Seasonal",
            "login": "qa_seasonal_theme",
            "password": "cositt_qa_1234",
            "group_ids": [Command.link(self.env.ref("base.group_user").id)],
        })
        self.authenticate(user.login, "cositt_qa_1234")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)

    def test_login_page_not_affected(self):
        # Este módulo es solo backend (web.assets_backend) — /web/login
        # no debe verse afectado en absoluto.
        self.env.company.write({"cositt_seasonal_theme_enabled": True})
        response = self.url_open("/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("cositt_seasonal_theme", response.text)
