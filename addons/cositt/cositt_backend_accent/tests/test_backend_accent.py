from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Command
from odoo.tests import HttpCase, tagged
from odoo.tests.common import TransactionCase


class TestCosittBackendAccent(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def _make_ordinary_user(self):
        user = self.env.ref("base.public_user")
        user.group_ids = [
            Command.unlink(self.env.ref("base.group_public").id),
            Command.link(self.env.ref("base.group_user").id),
        ]
        return user

    # --- valores por defecto: cero impacto sin configurar -------------

    def test_default_state_is_disabled(self):
        company = self.env["res.company"].create({"name": "QA Backend Accent Co"})
        self.assertFalse(company.cositt_backend_accent_enabled)
        self.assertFalse(company.cositt_backend_accent_color)

    def test_config_returns_false_when_disabled(self):
        self.company.cositt_backend_accent_color = "#e67e22"
        self.assertFalse(self.company.cositt_backend_accent_enabled)
        self.assertFalse(self.company._cositt_get_backend_accent_color())

    def test_config_returns_color_when_enabled(self):
        self.company.write({
            "cositt_backend_accent_enabled": True,
            "cositt_backend_accent_color": "#e67e22",
        })
        self.assertEqual(self.company._cositt_get_backend_accent_color(), "#e67e22")

    def test_config_returns_false_when_enabled_without_color(self):
        self.company.cositt_backend_accent_enabled = True
        self.assertFalse(self.company._cositt_get_backend_accent_color())

    # --- validación ------------------------------------------------------

    def test_invalid_color_format_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_backend_accent_color = "orange"

    def test_valid_color_format_is_accepted(self):
        self.company.cositt_backend_accent_color = "#ABCDEF"
        self.assertEqual(self.company.cositt_backend_accent_color, "#ABCDEF")

    # --- permisos: hereda el ACL/reglas ya existentes de res.company ---

    def test_ordinary_user_cannot_write_backend_accent_fields(self):
        user = self._make_ordinary_user()
        with self.assertRaises(AccessError):
            self.company.with_user(user).write({"cositt_backend_accent_enabled": True})

    def test_ordinary_user_can_read_backend_accent_fields(self):
        self.company.cositt_backend_accent_enabled = True
        user = self._make_ordinary_user()
        value = self.company.with_user(user).cositt_backend_accent_enabled
        self.assertTrue(value)

    # --- multiempresa --------------------------------------------------

    def test_each_company_has_independent_accent_color(self):
        other_company = self.env["res.company"].create({"name": "QA Backend Accent Co 2"})
        self.company.write({
            "cositt_backend_accent_enabled": True,
            "cositt_backend_accent_color": "#ff0000",
        })
        other_company.write({
            "cositt_backend_accent_enabled": True,
            "cositt_backend_accent_color": "#00ff00",
        })
        self.assertEqual(self.company._cositt_get_backend_accent_color(), "#ff0000")
        self.assertEqual(other_company._cositt_get_backend_accent_color(), "#00ff00")

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
class TestCosittBackendAccentHttp(HttpCase):
    """El color viaja en session_info() — verificar contra el HTML real
    de /odoo, no solo la función Python aislada (lección repetida en
    este proyecto: un error de wiring entre el modelo y la sesión no lo
    detecta un test unitario)."""

    def test_backend_session_info_omits_color_by_default(self):
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("cositt_backend_accent_color", response.text)

    def test_backend_session_info_includes_color_when_enabled(self):
        self.env.company.write({
            "cositt_backend_accent_enabled": True,
            "cositt_backend_accent_color": "#e67e22",
        })
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        self.assertIn('"cositt_backend_accent_color": "#e67e22"', response.text)

    def test_backend_loads_for_ordinary_user_when_enabled(self):
        self.env.company.write({
            "cositt_backend_accent_enabled": True,
            "cositt_backend_accent_color": "#e67e22",
        })
        user = self.env["res.users"].create({
            "name": "QA Backend Accent",
            "login": "qa_backend_accent",
            "password": "cositt_qa_1234",
            "group_ids": [Command.link(self.env.ref("base.group_user").id)],
        })
        self.authenticate(user.login, "cositt_qa_1234")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)

    def test_login_page_not_affected(self):
        # Este módulo es solo backend (web.assets_backend) — /web/login
        # no debe verse afectado en absoluto.
        self.env.company.write({
            "cositt_backend_accent_enabled": True,
            "cositt_backend_accent_color": "#e67e22",
        })
        response = self.url_open("/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("cositt_backend_accent", response.text)
