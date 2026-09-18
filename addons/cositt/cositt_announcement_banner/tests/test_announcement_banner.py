from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Command
from odoo.tests import HttpCase, tagged
from odoo.tests.common import TransactionCase


class TestCosittAnnouncementBanner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def setUp(self):
        super().setUp()
        # No asumir compañía limpia: cositt_plugins_dev es una base
        # compartida con verificación manual en navegador entre sesiones
        # (mismo hallazgo que en cositt_kanban_ribbon_theme) — se fuerza
        # un estado conocido en vez de depender de lo que haya quedado.
        self.company.write({
            "cositt_announcement_banner_enabled": False,
            "cositt_announcement_banner_message": False,
            "cositt_announcement_banner_style": "info",
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
        company = self.env["res.company"].create({"name": "QA Banner Co"})
        self.assertFalse(company.cositt_announcement_banner_enabled)
        self.assertFalse(company.cositt_announcement_banner_message)
        self.assertEqual(company.cositt_announcement_banner_style, "info")

    def test_config_returns_false_when_disabled(self):
        self.company.cositt_announcement_banner_message = "Mantenimiento el viernes"
        self.assertFalse(self.company.cositt_announcement_banner_enabled)
        self.assertFalse(self.company._cositt_get_announcement_banner_config())

    def test_config_returns_false_when_enabled_without_message(self):
        self.company.cositt_announcement_banner_enabled = True
        self.assertFalse(self.company._cositt_get_announcement_banner_config())

    def test_config_returns_false_when_message_is_only_whitespace(self):
        self.company.write({
            "cositt_announcement_banner_enabled": True,
            "cositt_announcement_banner_message": "   ",
        })
        self.assertFalse(self.company._cositt_get_announcement_banner_config())

    def test_config_message_is_stripped(self):
        self.company.write({
            "cositt_announcement_banner_enabled": True,
            "cositt_announcement_banner_message": "  Mantenimiento el viernes  ",
        })
        config = self.company._cositt_get_announcement_banner_config()
        self.assertEqual(config["message"], "Mantenimiento el viernes")

    def test_config_returns_dict_when_enabled_with_message(self):
        self.company.write({
            "cositt_announcement_banner_enabled": True,
            "cositt_announcement_banner_message": "Mantenimiento el viernes",
            "cositt_announcement_banner_style": "warning",
        })
        config = self.company._cositt_get_announcement_banner_config()
        self.assertEqual(config, {
            "message": "Mantenimiento el viernes",
            "style": "warning",
        })

    def test_config_defaults_to_info_style(self):
        self.company.write({
            "cositt_announcement_banner_enabled": True,
            "cositt_announcement_banner_message": "Aviso sin estilo elegido",
        })
        config = self.company._cositt_get_announcement_banner_config()
        self.assertEqual(config["style"], "info")

    # --- validación ------------------------------------------------------

    def test_message_over_max_length_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_announcement_banner_message = "x" * 301

    def test_message_at_max_length_is_accepted(self):
        message = "x" * 300
        self.company.cositt_announcement_banner_message = message
        self.assertEqual(self.company.cositt_announcement_banner_message, message)

    # --- permisos: hereda el ACL/reglas ya existentes de res.company ---

    def test_ordinary_user_cannot_write_banner_fields(self):
        user = self._make_ordinary_user()
        with self.assertRaises(AccessError):
            self.company.with_user(user).write({"cositt_announcement_banner_enabled": True})

    def test_ordinary_user_can_read_banner_fields(self):
        self.company.cositt_announcement_banner_enabled = True
        user = self._make_ordinary_user()
        value = self.company.with_user(user).cositt_announcement_banner_enabled
        self.assertTrue(value)

    # --- multiempresa --------------------------------------------------

    def test_each_company_has_independent_banner(self):
        other_company = self.env["res.company"].create({"name": "QA Banner Co 2"})
        self.company.write({
            "cositt_announcement_banner_enabled": True,
            "cositt_announcement_banner_message": "Aviso empresa 1",
        })
        other_company.write({
            "cositt_announcement_banner_enabled": True,
            "cositt_announcement_banner_message": "Aviso empresa 2",
        })
        self.assertEqual(
            self.company._cositt_get_announcement_banner_config()["message"], "Aviso empresa 1"
        )
        self.assertEqual(
            other_company._cositt_get_announcement_banner_config()["message"], "Aviso empresa 2"
        )

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
class TestCosittAnnouncementBannerHttp(HttpCase):
    """El aviso viaja en session_info() — verificar contra el HTML real
    de /odoo, no solo la función Python aislada (mismo criterio que
    cositt_backend_accent: un error de wiring entre el modelo y la
    sesión no lo detecta un test unitario)."""

    def test_backend_session_info_omits_banner_by_default(self):
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("cositt_announcement_banner", response.text)

    def test_backend_session_info_includes_banner_when_enabled(self):
        self.env.company.write({
            "cositt_announcement_banner_enabled": True,
            "cositt_announcement_banner_message": "Mantenimiento el viernes",
            "cositt_announcement_banner_style": "danger",
        })
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        self.assertIn('"cositt_announcement_banner"', response.text)
        self.assertIn("Mantenimiento el viernes", response.text)
        self.assertIn('"style": "danger"', response.text)

    def test_backend_loads_for_ordinary_user_when_enabled(self):
        self.env.company.write({
            "cositt_announcement_banner_enabled": True,
            "cositt_announcement_banner_message": "Mantenimiento el viernes",
        })
        user = self.env["res.users"].create({
            "name": "QA Banner",
            "login": "qa_announcement_banner",
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
            "cositt_announcement_banner_enabled": True,
            "cositt_announcement_banner_message": "Mantenimiento el viernes",
        })
        response = self.url_open("/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("cositt_announcement_banner", response.text)
