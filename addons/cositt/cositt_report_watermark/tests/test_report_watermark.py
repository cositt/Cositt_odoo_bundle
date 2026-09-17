from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestCosittReportWatermark(TransactionCase):
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

    def test_default_state_is_disabled_and_visually_neutral(self):
        company = self.env["res.company"].create({"name": "QA Watermark Co"})
        self.assertFalse(company.cositt_watermark_enabled)
        self.assertFalse(company.cositt_watermark_text)
        self.assertEqual(company.cositt_watermark_opacity, 12)
        self.assertEqual(company.cositt_watermark_rotation, -45)

    def test_config_reports_disabled_by_default(self):
        self.assertEqual(
            self.company._cositt_get_watermark_config(), {"enabled": False}
        )

    # --- activación y valores -------------------------------------------

    def test_valid_config_is_reflected(self):
        self.company.write({
            "cositt_watermark_enabled": True,
            "cositt_watermark_text": "BORRADOR",
            "cositt_watermark_opacity": 20,
            "cositt_watermark_rotation": -30,
        })
        config = self.company._cositt_get_watermark_config()
        self.assertEqual(config, {
            "enabled": True,
            "text": "BORRADOR",
            "opacity_ratio": 0.2,
            "rotation": -30,
        })

    # --- validaciones ----------------------------------------------------

    def test_enabling_without_text_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.write({
                "cositt_watermark_enabled": True,
                "cositt_watermark_text": False,
            })

    def test_opacity_out_of_range_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_watermark_opacity = 101

    def test_opacity_negative_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_watermark_opacity = -1

    def test_opacity_boundary_values_are_accepted(self):
        self.company.cositt_watermark_opacity = 0
        self.assertEqual(self.company.cositt_watermark_opacity, 0)
        self.company.cositt_watermark_opacity = 100
        self.assertEqual(self.company.cositt_watermark_opacity, 100)

    def test_rotation_out_of_range_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_watermark_rotation = 181

    def test_rotation_boundary_values_are_accepted(self):
        self.company.cositt_watermark_rotation = -180
        self.assertEqual(self.company.cositt_watermark_rotation, -180)
        self.company.cositt_watermark_rotation = 180
        self.assertEqual(self.company.cositt_watermark_rotation, 180)

    # --- reset -------------------------------------------------------------

    def test_reset_restores_all_defaults(self):
        self.company.write({
            "cositt_watermark_enabled": True,
            "cositt_watermark_text": "COPIA",
            "cositt_watermark_opacity": 50,
            "cositt_watermark_rotation": 10,
        })

        self.company.action_cositt_reset_watermark()

        self.assertFalse(self.company.cositt_watermark_enabled)
        self.assertFalse(self.company.cositt_watermark_text)
        self.assertEqual(self.company.cositt_watermark_opacity, 12)
        self.assertEqual(self.company.cositt_watermark_rotation, -45)

    # --- permisos: hereda el ACL/reglas ya existentes de res.company ---

    def test_ordinary_user_cannot_write_watermark_fields(self):
        user = self._make_ordinary_user()
        with self.assertRaises(AccessError):
            self.company.with_user(user).write({"cositt_watermark_enabled": True})

    def test_ordinary_user_can_read_watermark_fields(self):
        self.company.write({
            "cositt_watermark_enabled": True,
            "cositt_watermark_text": "BORRADOR",
        })
        user = self._make_ordinary_user()
        value = self.company.with_user(user).cositt_watermark_enabled
        self.assertTrue(value)

    # --- multiempresa -----------------------------------------------------

    def test_each_company_has_independent_watermark_config(self):
        other_company = self.env["res.company"].create({"name": "QA Watermark Co 2"})
        self.company.write({
            "cositt_watermark_enabled": True,
            "cositt_watermark_text": "BORRADOR",
        })
        other_company.write({
            "cositt_watermark_enabled": True,
            "cositt_watermark_text": "COPIA",
        })

        self.assertEqual(
            self.company._cositt_get_watermark_config()["text"], "BORRADOR"
        )
        self.assertEqual(
            other_company._cositt_get_watermark_config()["text"], "COPIA"
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
class TestCosittReportWatermarkRendering(TransactionCase):
    """Renderiza un reporte PDF REAL (base.report_irmodulereference,
    del propio módulo base — sin depender de `account`, bloqueado en
    este entorno, ver CLAUDE.md) para confirmar que la marca de agua
    aparece en el HTML/PDF de verdad, no solo en la función Python
    aislada (lección de cositt_login_background)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_ref = "base.report_irmodulereference"
        cls.module = cls.env["ir.module.module"].search([], limit=1)

    def test_watermark_absent_by_default_in_rendered_html(self):
        self.env.company.cositt_watermark_enabled = False
        html, _report_type = self.env["ir.actions.report"]._render_qweb_html(
            self.report_ref, self.module.ids
        )
        self.assertNotIn(b"o_cositt_watermark", html)

    def test_watermark_present_in_rendered_html_when_enabled(self):
        self.env.company.write({
            "cositt_watermark_enabled": True,
            "cositt_watermark_text": "BORRADOR QA",
        })
        html, _report_type = self.env["ir.actions.report"]._render_qweb_html(
            self.report_ref, self.module.ids
        )
        self.assertIn(b"o_cositt_watermark", html)
        self.assertIn(b"BORRADOR QA", html)

    def test_watermark_survives_real_wkhtmltopdf_render(self):
        # No solo el HTML intermedio: el binario real de wkhtmltopdf
        # (disponible en este entorno) debe poder procesar el markup
        # sin romperse.
        #
        # Hallazgo real (no supuesto): en modo test, Odoo salta
        # wkhtmltopdf a propósito y devuelve HTML en su lugar
        # (`_pre_render_qweb_pdf`, condición `test_enable and not
        # force_report_rendering`) — para forzar el render real hace
        # falta este contexto explícito.
        self.env.company.write({
            "cositt_watermark_enabled": True,
            "cositt_watermark_text": "BORRADOR QA",
        })
        pdf_content, report_type = self.env["ir.actions.report"].with_context(
            force_report_rendering=True
        )._render_qweb_pdf(self.report_ref, self.module.ids)
        self.assertEqual(report_type, "pdf")
        self.assertTrue(pdf_content)
        self.assertTrue(pdf_content.startswith(b"%PDF"))
