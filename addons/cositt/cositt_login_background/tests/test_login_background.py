import base64
import io
import os

from PIL import Image as PILImage

from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Command
from odoo.tests import HttpCase, tagged
from odoo.tests.common import TransactionCase


def _make_jpeg_bytes(size=(40, 30)):
    buffer = io.BytesIO()
    PILImage.new("RGB", size, color=(10, 20, 30)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _make_png_bytes(size=(40, 30)):
    buffer = io.BytesIO()
    PILImage.new("RGB", size, color=(200, 100, 50)).save(buffer, format="PNG")
    return buffer.getvalue()


def _make_webp_bytes():
    # NO se genera con PIL en este proceso a propósito: Odoo endurece
    # Pillow por seguridad (odoo/tools/image.py hace `Image.preinit()`
    # + `Image._initialized = 2`, que registra solo un subconjunto
    # mínimo de formatos y evita el auto-registro completo bajo
    # demanda) — dentro del proceso de Odoo, `Image.new(...).save(...,
    # format="WEBP")` falla con `KeyError: 'WEBP'` (comprobado: falla
    # aquí, funciona en un proceso python3 aparte). Se usa en cambio un
    # WEBP real de 40x30 generado UNA VEZ fuera de Odoo y embebido como
    # bytes fijos, para probar el camino real sin depender de que
    # Pillow pueda codificar el formato en este proceso.
    return base64.b64decode(
        b"UklGRjQAAABXRUJQVlA4ICgAAADwAgCdASooAB4APm02l0ikIyIhJWgAgA2JaQAAKUNt8AD++3jAAAAA"
    )


def _make_oversized_png_bytes():
    # Ruido aleatorio: comprime muy mal en PNG, así el archivo final se
    # queda por encima de MAX_LOGIN_BG_BYTES incluso después del resize
    # automático de fields.Image (mismo hallazgo que en
    # cositt_home_wallpaper: hay que probar el límite de verdad, no solo
    # confiar en que "una imagen grande" lo sea después de procesarse).
    width, height = 2000, 1400
    random_bytes = os.urandom(width * height * 3)
    buffer = io.BytesIO()
    PILImage.frombytes("RGB", (width, height), random_bytes).save(buffer, format="PNG")
    return buffer.getvalue()


class TestCosittLoginBackground(TransactionCase):
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
        company = self.env["res.company"].create({"name": "QA Login BG Co"})
        self.assertFalse(company.cositt_login_bg_enabled)
        self.assertFalse(company.cositt_login_bg_image)
        self.assertEqual(company.cositt_login_bg_overlay, 25)
        self.assertEqual(company.cositt_login_bg_blur, 0)
        self.assertEqual(company.cositt_login_bg_fit, "cover")
        self.assertEqual(company.cositt_login_bg_position, "center")

    def test_config_reports_disabled_by_default(self):
        config = self.company._cositt_get_login_bg_config()
        self.assertEqual(config, {"enabled": False})

    # --- activación y valores -------------------------------------------

    def test_enabling_without_image_reports_none_css_image(self):
        self.company.cositt_login_bg_enabled = True
        config = self.company._cositt_get_login_bg_config()
        self.assertTrue(config["enabled"])
        self.assertEqual(config["css_image"], "none")

    def test_uploading_valid_jpeg_builds_css_url(self):
        self.company.write({
            "cositt_login_bg_enabled": True,
            "cositt_login_bg_image": base64.b64encode(_make_jpeg_bytes()),
        })
        config = self.company._cositt_get_login_bg_config()
        self.assertEqual(
            config["css_image"],
            'url("/web/image/res.company/%s/cositt_login_bg_image")' % self.company.id,
        )

    def test_config_maps_fit_and_position_to_css(self):
        self.company.write({
            "cositt_login_bg_enabled": True,
            "cositt_login_bg_color": "#112233",
            "cositt_login_bg_overlay": 40,
            "cositt_login_bg_blur": 8,
            "cositt_login_bg_fit": "contain",
            "cositt_login_bg_position": "top",
        })
        config = self.company._cositt_get_login_bg_config()
        self.assertEqual(config["color"], "#112233")
        self.assertEqual(config["css_size"], "contain")
        self.assertEqual(config["css_position"], "center top")
        self.assertEqual(config["blur"], 8)
        self.assertEqual(config["overlay_ratio"], 0.4)

    def test_disabled_color_defaults_to_transparent(self):
        self.company.cositt_login_bg_enabled = True
        config = self.company._cositt_get_login_bg_config()
        self.assertEqual(config["color"], "transparent")

    # --- validaciones ----------------------------------------------------

    def test_svg_content_is_rejected(self):
        # Mismo hallazgo que cositt_home_wallpaper: fields.Image no
        # rechaza SVG por sí solo (ImageProcess lo deja pasar sin
        # procesar). Se valida el mimetype real explícitamente.
        svg_bytes = b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"
        with self.assertRaises(ValidationError):
            self.company.write({
                "cositt_login_bg_image": base64.b64encode(svg_bytes),
            })

    def test_oversized_image_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.write({
                "cositt_login_bg_image": base64.b64encode(_make_oversized_png_bytes()),
            })

    def test_overlay_out_of_range_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_login_bg_overlay = 101

    def test_overlay_negative_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_login_bg_overlay = -1

    def test_overlay_boundary_values_are_accepted(self):
        # 0 y 100 son límites inclusive — un `<`/`<=` mal puesto en el
        # constrains los rechazaría por error.
        self.company.cositt_login_bg_overlay = 0
        self.assertEqual(self.company.cositt_login_bg_overlay, 0)
        self.company.cositt_login_bg_overlay = 100
        self.assertEqual(self.company.cositt_login_bg_overlay, 100)

    def test_blur_out_of_range_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_login_bg_blur = 999

    def test_blur_boundary_value_is_accepted(self):
        self.company.cositt_login_bg_blur = 40  # MAX_LOGIN_BG_BLUR
        self.assertEqual(self.company.cositt_login_bg_blur, 40)

    def test_invalid_color_format_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.cositt_login_bg_color = "blue"

    def test_valid_color_format_is_accepted(self):
        self.company.cositt_login_bg_color = "#ABCDEF"
        self.assertEqual(self.company.cositt_login_bg_color, "#ABCDEF")

    def test_png_upload_is_accepted(self):
        self.company.write({
            "cositt_login_bg_image": base64.b64encode(_make_png_bytes()),
        })
        self.assertTrue(self.company.cositt_login_bg_image)

    def test_webp_upload_is_accepted(self):
        self.company.write({
            "cositt_login_bg_image": base64.b64encode(_make_webp_bytes()),
        })
        self.assertTrue(self.company.cositt_login_bg_image)

    # --- reset -------------------------------------------------------------

    def test_reset_restores_all_defaults(self):
        self.company.write({
            "cositt_login_bg_enabled": True,
            "cositt_login_bg_image": base64.b64encode(_make_jpeg_bytes()),
            "cositt_login_bg_color": "#010203",
            "cositt_login_bg_overlay": 80,
            "cositt_login_bg_blur": 20,
            "cositt_login_bg_fit": "stretch",
            "cositt_login_bg_position": "bottom",
        })

        self.company.action_cositt_reset_login_bg()

        self.assertFalse(self.company.cositt_login_bg_enabled)
        self.assertFalse(self.company.cositt_login_bg_image)
        self.assertFalse(self.company.cositt_login_bg_color)
        self.assertEqual(self.company.cositt_login_bg_overlay, 25)
        self.assertEqual(self.company.cositt_login_bg_blur, 0)
        self.assertEqual(self.company.cositt_login_bg_fit, "cover")
        self.assertEqual(self.company.cositt_login_bg_position, "center")

    # --- permisos: hereda el ACL/reglas ya existentes de res.company ---

    def test_ordinary_user_cannot_write_login_bg_fields(self):
        user = self._make_ordinary_user()
        with self.assertRaises(AccessError):
            self.company.with_user(user).write({"cositt_login_bg_enabled": True})

    def test_ordinary_user_can_read_login_bg_fields(self):
        self.company.cositt_login_bg_enabled = True
        user = self._make_ordinary_user()
        value = self.company.with_user(user).cositt_login_bg_enabled
        self.assertTrue(value)

    # --- multiempresa --------------------------------------------------

    def test_each_company_has_independent_login_bg_config(self):
        other_company = self.env["res.company"].create({"name": "QA Login BG Co 2"})
        self.company.write({
            "cositt_login_bg_enabled": True,
            "cositt_login_bg_color": "#ff0000",
        })
        other_company.write({
            "cositt_login_bg_enabled": True,
            "cositt_login_bg_color": "#00ff00",
        })

        config_a = self.company._cositt_get_login_bg_config()
        config_b = other_company._cositt_get_login_bg_config()

        self.assertEqual(config_a["color"], "#ff0000")
        self.assertEqual(config_b["color"], "#00ff00")
        # Esto prueba que el MÉTODO es correcto por compañía, no que un
        # visitante anónimo real llegue a ver la de "other_company": ver
        # limitación documentada en _cositt_get_login_bg_config() y en
        # el README (request.env.company, para un visitante anónimo,
        # resuelve siempre a la compañía de base.public_user, no a una
        # elegida en el momento del login).

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
class TestCosittLoginBackgroundHttp(HttpCase):
    """Smoke tests de integración real contra /web/login (server-rendered,
    sin JS): confirman que el fondo aparece SOLO en login cuando está
    activo, y que login sigue viéndose neutro por defecto."""

    def test_login_page_neutral_by_default(self):
        response = self.url_open("/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('id="o_cositt_login_bg"', response.text)

    def test_login_page_shows_background_when_enabled(self):
        self.env.company.write({
            "cositt_login_bg_enabled": True,
            "cositt_login_bg_color": "#112233",
            "cositt_login_bg_image": base64.b64encode(_make_jpeg_bytes()),
        })
        response = self.url_open("/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="o_cositt_login_bg"', response.text)
        self.assertIn("--cositt-login-bg-color: #112233", response.text)
        # Regresión directa de un bug real: t-esc/t-out con escapado
        # normal convertía las comillas de url("...") en &#34; literal
        # — como <style> es "raw text" en HTML, el navegador no las
        # decodifica, y la imagen de fondo no cargaba nunca aunque la
        # config fuera correcta. Debe verse la comilla real, no la
        # entidad HTML.
        self.assertIn(
            '--cositt-login-bg-image: url("/web/image/res.company/%s/cositt_login_bg_image")'
            % self.env.company.id,
            response.text,
        )
        self.assertNotIn("&#34;", response.text)

    def test_uploaded_image_is_servable_to_anonymous_visitor(self):
        # No basta con comprobar que la URL se construye bien
        # (_cositt_get_login_bg_config): un visitante de /web/login
        # nunca está autenticado, así que lo que importa de verdad es
        # que /web/image/... responda 200 SIN sesión — confirma que el
        # ACL de lectura de res.company (abierto de fábrica, sin sudo)
        # también cubre este acceso real, no solo el cálculo del texto.
        self.env.company.write({
            "cositt_login_bg_enabled": True,
            "cositt_login_bg_image": base64.b64encode(_make_jpeg_bytes()),
        })
        image_url = self.env.company._cositt_get_login_bg_config()["css_image"]
        # css_image viene como 'url("/web/image/...")' — se extrae la
        # ruta real para pedirla como visitante anónimo de verdad.
        path = image_url.split('"')[1]
        response = self.url_open(path)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content)

    def test_login_successful_page_not_broken_when_enabled(self):
        # login_successful está en el alcance documentado (interstitial
        # del mismo flujo de autenticación) — debe seguir funcionando
        # sin traceback y mostrar el marcador también ahí.
        self.env.company.write({"cositt_login_bg_enabled": True})
        self.authenticate("admin", "admin")
        response = self.url_open("/web/login_successful")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="o_cositt_login_bg"', response.text)

    def test_backend_home_menu_not_affected_when_enabled(self):
        # Regresión directa del bug real encontrado en verificación
        # manual: web_enterprise hereda TAMBIÉN web.login_layout y
        # pisa body_classname con su propio t-set incondicional (razón
        # por la que este módulo ancla en web.layout + el path HTTP en
        # vez de en una clase de body — ver views/webclient_templates.xml).
        # Este test confirma que, con web_enterprise instalado en este
        # entorno, el marcador de fondo NO se cuela en el Home Menu ni
        # en el resto del backend.
        self.env.company.write({"cositt_login_bg_enabled": True})
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("o_cositt_login_bg", response.text)
