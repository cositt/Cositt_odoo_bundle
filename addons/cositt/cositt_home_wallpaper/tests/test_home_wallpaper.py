import base64
import io
import os

from PIL import Image as PILImage

from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Command
from odoo.tests.common import TransactionCase


def _make_jpeg_bytes(size=(40, 30)):
    buffer = io.BytesIO()
    PILImage.new("RGB", size, color=(10, 20, 30)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _make_oversized_png_bytes():
    # Ruido aleatorio: comprime muy mal en PNG (sin patrones repetibles),
    # así el archivo final se queda por encima de MAX_WALLPAPER_BYTES
    # incluso después del resize automático de fields.Image — necesario
    # para probar el límite de verdad, no solo confiar en que "una
    # imagen grande" lo sea después de procesarse.
    width, height = 2000, 1400
    random_bytes = os.urandom(width * height * 3)
    buffer = io.BytesIO()
    PILImage.frombytes("RGB", (width, height), random_bytes).save(buffer, format="PNG")
    return buffer.getvalue()


class TestCosittHomeWallpaper(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.admin = cls.env.ref("base.user_admin")

    def _make_ordinary_user(self):
        user = self.env.ref("base.public_user")
        user.group_ids = [
            Command.unlink(self.env.ref("base.group_public").id),
            Command.link(self.env.ref("base.group_user").id),
        ]
        return user

    # --- valores por defecto: cero impacto visual sin configurar -------

    def test_default_state_is_disabled_and_visually_neutral(self):
        # Empresa recién creada, módulo instalado, nada tocado a mano.
        company = self.env["res.company"].create({"name": "QA Wallpaper Co"})
        self.assertFalse(company.cositt_wallpaper_enabled)
        self.assertFalse(company.cositt_wallpaper_image)
        self.assertEqual(company.cositt_wallpaper_overlay, 25)
        self.assertEqual(company.cositt_wallpaper_blur, 0)
        self.assertEqual(company.cositt_wallpaper_fit, "cover")
        self.assertEqual(company.cositt_wallpaper_position, "center")

    def test_session_info_reports_disabled_by_default(self):
        config = self.company._cositt_get_wallpaper_config()
        self.assertEqual(config, {"enabled": False})

    # --- activación y valores -------------------------------------------

    def test_enabling_without_image_reports_no_image_url(self):
        self.company.cositt_wallpaper_enabled = True
        config = self.company._cositt_get_wallpaper_config()
        self.assertTrue(config["enabled"])
        self.assertFalse(config["image_url"])

    def test_uploading_valid_jpeg_is_accepted_and_url_is_built(self):
        self.company.write({
            "cositt_wallpaper_enabled": True,
            "cositt_wallpaper_image": base64.b64encode(_make_jpeg_bytes()),
        })
        config = self.company._cositt_get_wallpaper_config()
        self.assertEqual(
            config["image_url"],
            "/web/image/res.company/%s/cositt_wallpaper_image" % self.company.id,
        )

    def test_session_info_reflects_all_configured_values(self):
        self.company.write({
            "cositt_wallpaper_enabled": True,
            "cositt_wallpaper_color": "#112233",
            "cositt_wallpaper_overlay": 40,
            "cositt_wallpaper_blur": 8,
            "cositt_wallpaper_fit": "contain",
            "cositt_wallpaper_position": "top",
        })
        config = self.company._cositt_get_wallpaper_config()
        self.assertEqual(config["color"], "#112233")
        self.assertEqual(config["overlay"], 40)
        self.assertEqual(config["blur"], 8)
        self.assertEqual(config["fit"], "contain")
        self.assertEqual(config["position"], "top")

    # --- validaciones ------------------------------------------------------

    def test_svg_content_is_rejected(self):
        # Hallazgo real (no asumido): odoo.tools.image.ImageProcess deja
        # pasar SVG SIN procesar a propósito (mira el propio código
        # fuente: "don't process... if the image is SVG"), no lo
        # rechaza por sí solo. Por eso este módulo valida el mimetype
        # real explícitamente (ver _check_cositt_wallpaper_image) — sin
        # esa validación propia, un SVG (que puede llevar JavaScript
        # embebido) se habría guardado tal cual sin ningún aviso.
        svg_bytes = b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"
        with self.assertRaises(ValidationError):
            self.company.write({
                "cositt_wallpaper_image": base64.b64encode(svg_bytes),
            })

    def test_oversized_image_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.write({
                "cositt_wallpaper_image": base64.b64encode(_make_oversized_png_bytes()),
            })

    def test_overlay_out_of_range_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_wallpaper_overlay = 101

    def test_overlay_negative_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_wallpaper_overlay = -1

    def test_blur_out_of_range_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_wallpaper_blur = 999

    def test_invalid_color_format_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_wallpaper_color = "blue"

    def test_valid_color_format_is_accepted(self):
        self.company.cositt_wallpaper_color = "#ABCDEF"
        self.assertEqual(self.company.cositt_wallpaper_color, "#ABCDEF")

    # --- reset ---------------------------------------------------------

    def test_reset_restores_all_defaults(self):
        self.company.write({
            "cositt_wallpaper_enabled": True,
            "cositt_wallpaper_image": base64.b64encode(_make_jpeg_bytes()),
            "cositt_wallpaper_color": "#010203",
            "cositt_wallpaper_overlay": 80,
            "cositt_wallpaper_blur": 20,
            "cositt_wallpaper_fit": "stretch",
            "cositt_wallpaper_position": "bottom",
        })

        self.company.action_cositt_reset_wallpaper()

        self.assertFalse(self.company.cositt_wallpaper_enabled)
        self.assertFalse(self.company.cositt_wallpaper_image)
        self.assertFalse(self.company.cositt_wallpaper_color)
        self.assertEqual(self.company.cositt_wallpaper_overlay, 25)
        self.assertEqual(self.company.cositt_wallpaper_blur, 0)
        self.assertEqual(self.company.cositt_wallpaper_fit, "cover")
        self.assertEqual(self.company.cositt_wallpaper_position, "center")

    # --- permisos: hereda el ACL/reglas ya existentes de res.company ---

    def test_ordinary_user_cannot_write_wallpaper_fields(self):
        user = self._make_ordinary_user()
        with self.assertRaises(AccessError):
            self.company.with_user(user).write({"cositt_wallpaper_enabled": True})

    def test_ordinary_user_can_read_wallpaper_fields(self):
        self.company.cositt_wallpaper_enabled = True
        user = self._make_ordinary_user()
        # No debe lanzar: la lectura de res.company ya es abierta de
        # fábrica (confirmado en base/security/ir.model.access.csv,
        # group_public incluido) — este módulo no la amplía ni la
        # restringe, solo se apoya en ella.
        value = self.company.with_user(user).cositt_wallpaper_enabled
        self.assertTrue(value)

    # --- multiempresa -----------------------------------------------------

    def test_each_company_has_independent_wallpaper_config(self):
        other_company = self.env["res.company"].create({"name": "QA Wallpaper Co 2"})
        self.company.write({
            "cositt_wallpaper_enabled": True,
            "cositt_wallpaper_color": "#ff0000",
        })
        other_company.write({
            "cositt_wallpaper_enabled": True,
            "cositt_wallpaper_color": "#00ff00",
        })

        config_a = self.company._cositt_get_wallpaper_config()
        config_b = other_company._cositt_get_wallpaper_config()

        self.assertEqual(config_a["color"], "#ff0000")
        self.assertEqual(config_b["color"], "#00ff00")

    # session_info() en sí (el método de ir.http, no
    # _cositt_get_wallpaper_config()) necesita un request HTTP real
    # (lee request.session.uid) — no se puede invocar de forma aislada
    # en un TransactionCase. Que usa la compañía activa correcta queda
    # cubierto por _cositt_get_wallpaper_config() (probado arriba con
    # dos compañías) más la verificación manual en navegador real
    # (cambio de compañía → recarga → fondo correcto).

    # --- código -------------------------------------------------------------

    def test_module_never_calls_sudo(self):
        from pathlib import Path

        module_dir = Path(__file__).resolve().parent.parent
        for path in (module_dir / "models").glob("*.py"):
            self.assertNotIn(
                ".sudo(", path.read_text(encoding="utf-8"),
                "%s no debería usar sudo()" % path.name,
            )
