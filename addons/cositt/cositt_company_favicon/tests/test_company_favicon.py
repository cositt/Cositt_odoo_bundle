import base64
import io

from PIL import Image as PILImage

from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Command
from odoo.tests import HttpCase, tagged
from odoo.tests.common import TransactionCase


def _make_png_bytes(size=(64, 64)):
    buffer = io.BytesIO()
    PILImage.new("RGBA", size, color=(200, 100, 50, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def _make_jpeg_bytes(size=(64, 64)):
    buffer = io.BytesIO()
    PILImage.new("RGB", size, color=(10, 20, 30)).save(buffer, format="JPEG")
    return buffer.getvalue()


class TestCosittCompanyFavicon(TransactionCase):
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
        company = self.env["res.company"].create({"name": "QA Favicon Co"})
        self.assertFalse(company.cositt_branding_enabled)
        self.assertFalse(company.cositt_favicon_image)
        self.assertFalse(company.cositt_browser_title)

    def test_favicon_url_false_when_disabled(self):
        self.company.write({
            "cositt_favicon_image": base64.b64encode(_make_png_bytes()),
        })
        self.assertFalse(self.company.cositt_branding_enabled)
        self.assertFalse(self.company._cositt_get_favicon_url())

    def test_favicon_url_false_when_enabled_without_image(self):
        self.company.cositt_branding_enabled = True
        self.assertFalse(self.company._cositt_get_favicon_url())

    def test_favicon_url_present_when_configured(self):
        self.company.write({
            "cositt_branding_enabled": True,
            "cositt_favicon_image": base64.b64encode(_make_png_bytes()),
        })
        self.assertEqual(
            self.company._cositt_get_favicon_url(),
            "/web/image/res.company/%s/cositt_favicon_image" % self.company.id,
        )

    def test_browser_title_false_when_disabled(self):
        self.company.cositt_browser_title = "Cositt ERP"
        self.assertFalse(self.company._cositt_get_browser_title())

    def test_browser_title_present_when_configured(self):
        self.company.write({
            "cositt_branding_enabled": True,
            "cositt_browser_title": "Cositt ERP",
        })
        self.assertEqual(self.company._cositt_get_browser_title(), "Cositt ERP")

    # --- validaciones ----------------------------------------------------

    def test_jpeg_favicon_is_rejected(self):
        # Solo PNG a propósito (formato recomendado para favicons
        # modernos, sin ambigüedad de transparencia como JPEG) — ver
        # README.
        with self.assertRaises(ValidationError):
            self.company.write({
                "cositt_favicon_image": base64.b64encode(_make_jpeg_bytes()),
            })

    def test_svg_content_is_rejected(self):
        # Mismo hallazgo que cositt_home_wallpaper/cositt_login_background:
        # fields.Image no rechaza SVG por sí solo.
        svg_bytes = b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"
        with self.assertRaises(ValidationError):
            self.company.write({
                "cositt_favicon_image": base64.b64encode(svg_bytes),
            })

    def test_png_favicon_is_accepted(self):
        self.company.write({
            "cositt_favicon_image": base64.b64encode(_make_png_bytes()),
        })
        self.assertTrue(self.company.cositt_favicon_image)

    def test_browser_title_too_long_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_browser_title = "x" * 61

    def test_browser_title_boundary_length_is_accepted(self):
        self.company.cositt_browser_title = "x" * 60
        self.assertEqual(len(self.company.cositt_browser_title), 60)

    # --- permisos: hereda el ACL/reglas ya existentes de res.company ---

    def test_ordinary_user_cannot_write_favicon_fields(self):
        user = self._make_ordinary_user()
        with self.assertRaises(AccessError):
            self.company.with_user(user).write({"cositt_branding_enabled": True})

    def test_ordinary_user_can_read_favicon_fields(self):
        self.company.cositt_branding_enabled = True
        user = self._make_ordinary_user()
        value = self.company.with_user(user).cositt_branding_enabled
        self.assertTrue(value)

    # --- multiempresa --------------------------------------------------

    def test_each_company_has_independent_branding(self):
        other_company = self.env["res.company"].create({"name": "QA Favicon Co 2"})
        self.company.write({
            "cositt_branding_enabled": True,
            "cositt_browser_title": "Cositt ERP",
        })
        other_company.write({
            "cositt_branding_enabled": True,
            "cositt_browser_title": "Other Brand",
        })
        self.assertEqual(self.company._cositt_get_browser_title(), "Cositt ERP")
        self.assertEqual(other_company._cositt_get_browser_title(), "Other Brand")

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
class TestCosittCompanyFaviconHttp(HttpCase):
    """El favicon/título se sirven en HTML servidor (web.layout, todas
    las páginas) — verificar contra respuestas HTTP reales, no solo la
    función Python aislada."""

    def test_login_page_uses_default_favicon_and_title_by_default(self):
        response = self.url_open("/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn("/web/static/img/favicon.ico", response.text)
        self.assertIn("<title>Odoo</title>", response.text)

    def test_login_page_uses_custom_favicon_and_title_when_configured(self):
        self.env.company.write({
            "cositt_branding_enabled": True,
            "cositt_favicon_image": base64.b64encode(_make_png_bytes()),
            "cositt_browser_title": "Cositt ERP",
        })
        response = self.url_open("/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "/web/image/res.company/%s/cositt_favicon_image" % self.env.company.id,
            response.text,
        )
        self.assertIn("<title>Cositt ERP</title>", response.text)
        self.assertNotIn("/web/static/img/favicon.ico", response.text)

    def test_favicon_is_servable_to_anonymous_visitor(self):
        self.env.company.write({
            "cositt_branding_enabled": True,
            "cositt_favicon_image": base64.b64encode(_make_png_bytes()),
        })
        path = self.env.company._cositt_get_favicon_url()
        response = self.url_open(path)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content)

    def test_backend_session_info_includes_title_when_enabled(self):
        self.env.company.write({
            "cositt_branding_enabled": True,
            "cositt_browser_title": "Cositt ERP",
        })
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        self.assertIn('"cositt_browser_title": "Cositt ERP"', response.text)

    def test_scoped_app_title_and_icon_not_clobbered(self):
        # Regresión directa de un bug real (code review): un primer
        # diseño ponía el valor de este módulo con PRIORIDAD sobre
        # cualquier x_icon/title ya fijado por otra ruta — /scoped_app
        # (la página "Añadir a la pantalla de inicio" de PWA) fija los
        # suyos ANTES de que esta plantilla corra, y quedaban pisados.
        self.env.company.write({
            "cositt_branding_enabled": True,
            "cositt_favicon_image": base64.b64encode(_make_png_bytes()),
            "cositt_browser_title": "Cositt ERP",
        })
        modules = self.env["ir.module.module"].search(
            [("name", "=", "mail"), ("state", "=", "installed")], limit=1
        )
        if not modules:
            self.skipTest("módulo 'mail' no instalado en este entorno")
        response = self.url_open("/scoped_app?app_id=mail&app_name=Discuss")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("<title>Cositt ERP</title>", response.text)
        self.assertNotIn(
            "/web/image/res.company/%s/cositt_favicon_image" % self.env.company.id,
            response.text,
        )

    def test_backend_loads_for_ordinary_user_when_enabled(self):
        self.env.company.write({
            "cositt_branding_enabled": True,
            "cositt_browser_title": "Cositt ERP",
            "cositt_favicon_image": base64.b64encode(_make_png_bytes()),
        })
        user = self.env["res.users"].create({
            "name": "QA Company Favicon",
            "login": "qa_company_favicon",
            "password": "cositt_qa_1234",
            "group_ids": [Command.link(self.env.ref("base.group_user").id)],
        })
        self.authenticate(user.login, "cositt_qa_1234")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
