import base64
import re

from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Command
from odoo.tests.common import TransactionCase

# El fondo (<rect>) usa hsl(...) en el core o un hex de la paleta en
# este módulo; el texto (<text>) siempre trae fill='#ffffff' fijo en
# ambos casos — un regex genérico sobre todo el SVG capturaría ese
# blanco del texto y daría un falso verde. Hay que anclar al <rect>.
RECT_FILL_RE = re.compile(r"<rect fill='([^']+)'")


def _decode_svg(avatar_b64):
    return base64.b64decode(avatar_b64).decode()


class TestCosittAvatarStyle(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def setUp(self):
        super().setUp()
        # No asumir compañía limpia: cositt_plugins_dev es una base
        # compartida con verificación manual entre sesiones (mismo
        # hallazgo que en otros módulos de este proyecto).
        self.company.write({
            "cositt_avatar_style_enabled": False,
            "cositt_avatar_style_palette": "#714b67",
        })

    def _make_ordinary_user(self):
        user = self.env.ref("base.public_user")
        user.group_ids = [
            Command.unlink(self.env.ref("base.group_public").id),
            Command.link(self.env.ref("base.group_user").id),
        ]
        return user

    def _partner_without_image(self, name):
        return self.env["res.partner"].create({"name": name, "type": "contact"})

    # --- valores por defecto: cero impacto sin configurar -------------

    def test_default_state_is_disabled(self):
        company = self.env["res.company"].create({"name": "QA Avatar Co"})
        self.assertFalse(company.cositt_avatar_style_enabled)

    def test_palette_empty_when_disabled(self):
        self.assertEqual(self.company._cositt_get_avatar_palette(), [])

    def test_palette_returns_colors_when_enabled(self):
        self.company.write({
            "cositt_avatar_style_enabled": True,
            "cositt_avatar_style_palette": "#1e7d3c, #5b6bc0",
        })
        self.assertEqual(
            self.company._cositt_get_avatar_palette(), ["#1e7d3c", "#5b6bc0"]
        )

    # --- validación ------------------------------------------------------

    def test_invalid_color_in_palette_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.write({
                "cositt_avatar_style_enabled": True,
                "cositt_avatar_style_palette": "orange",
            })

    def test_one_invalid_color_among_valid_ones_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.write({
                "cositt_avatar_style_enabled": True,
                "cositt_avatar_style_palette": "#1e7d3c, notacolor",
            })

    def test_empty_palette_while_enabled_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.company.write({
                "cositt_avatar_style_enabled": True,
                "cositt_avatar_style_palette": "",
            })

    def test_garbage_palette_while_disabled_is_accepted(self):
        # Neutral por defecto: si está desactivado, no importa lo que
        # haya en el campo — no debería romper el guardado.
        self.company.write({
            "cositt_avatar_style_enabled": False,
            "cositt_avatar_style_palette": "orange, esto no es un color",
        })
        self.assertEqual(
            self.company.cositt_avatar_style_palette, "orange, esto no es un color"
        )

    # --- generación del SVG -----------------------------------------------

    def test_avatar_uses_core_default_when_disabled(self):
        partner = self._partner_without_image("Ana Paleta Test")
        svg = _decode_svg(partner.avatar_128)
        match = RECT_FILL_RE.search(svg)
        self.assertIsNotNone(match)
        # hsl(...) es el mecanismo nativo de Odoo — la garantía central
        # del módulo (desactivado = cero cambio de comportamiento).
        self.assertTrue(match.group(1).startswith("hsl("))

    def test_avatar_uses_brand_palette_when_enabled(self):
        self.company.write({
            "cositt_avatar_style_enabled": True,
            "cositt_avatar_style_palette": "#1e7d3c",
        })
        partner = self._partner_without_image("Ana Paleta Test")
        svg = _decode_svg(partner.avatar_128)
        self.assertIn("#1e7d3c", svg)

    def test_avatar_color_is_deterministic_per_name(self):
        self.company.write({
            "cositt_avatar_style_enabled": True,
            "cositt_avatar_style_palette": "#1e7d3c,#5b6bc0,#c2478a",
        })
        partner = self._partner_without_image("Bea Determinista Test")
        svg_first = _decode_svg(partner.avatar_128)
        partner.invalidate_recordset(["avatar_128"])
        svg_second = _decode_svg(partner.avatar_128)
        color_first = RECT_FILL_RE.search(svg_first).group(1)
        color_second = RECT_FILL_RE.search(svg_second).group(1)
        self.assertEqual(color_first, color_second)

    def test_avatar_palette_applies_to_hr_employee_too(self):
        # El override vive en avatar.mixin (no en res.partner
        # específicamente) — debe aplicar a cualquier modelo que lo
        # herede, no solo a Contactos.
        if "hr.employee" not in self.env:
            self.skipTest("módulo hr no instalado en esta base")
        self.company.write({
            "cositt_avatar_style_enabled": True,
            "cositt_avatar_style_palette": "#1e7d3c",
        })
        employee = self.env["hr.employee"].create({"name": "Empleado Paleta Test"})
        svg = _decode_svg(employee.avatar_128)
        self.assertIn("#1e7d3c", svg)

    # --- permisos: hereda el ACL/reglas ya existentes de res.company ---

    def test_ordinary_user_cannot_write_avatar_style_fields(self):
        user = self._make_ordinary_user()
        with self.assertRaises(AccessError):
            self.company.with_user(user).write({"cositt_avatar_style_enabled": True})

    def test_ordinary_user_can_read_avatar_style_fields(self):
        self.company.cositt_avatar_style_enabled = True
        user = self._make_ordinary_user()
        value = self.company.with_user(user).cositt_avatar_style_enabled
        self.assertTrue(value)

    # --- multiempresa: el color depende de la compañía activa del que mira, no del dueño del registro

    def test_avatar_color_depends_on_active_company_of_viewer(self):
        other_company = self.env["res.company"].create({
            "name": "QA Avatar Co 2",
            "cositt_avatar_style_enabled": True,
            "cositt_avatar_style_palette": "#5b6bc0",
        })
        self.company.write({
            "cositt_avatar_style_enabled": True,
            "cositt_avatar_style_palette": "#1e7d3c",
        })
        partner = self._partner_without_image("Multi Compania Test")
        svg_default_company = _decode_svg(partner.avatar_128)
        svg_other_company = _decode_svg(
            partner.with_company(other_company).avatar_128
        )
        self.assertIn("#1e7d3c", svg_default_company)
        self.assertIn("#5b6bc0", svg_other_company)

    # --- código -------------------------------------------------------------

    def test_module_never_calls_sudo(self):
        from pathlib import Path

        module_dir = Path(__file__).resolve().parent.parent
        for path in (module_dir / "models").glob("*.py"):
            self.assertNotIn(
                ".sudo(", path.read_text(encoding="utf-8"),
                "%s no debería usar sudo()" % path.name,
            )
