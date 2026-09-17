import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

COLOR_HEX_RE = re.compile(r"\A#[0-9A-Fa-f]{6}\Z")


class ResCompany(models.Model):
    _inherit = "res.company"

    cositt_backend_accent_enabled = fields.Boolean(
        string="Acento de backend activo",
        default=False,
        help="Mientras esté desactivado, el backend se ve exactamente "
        "igual que sin este módulo instalado.",
    )
    cositt_backend_accent_color = fields.Char(
        string="Color de acento de backend",
        help="Color hexadecimal (#rrggbb) para botones primarios, "
        "checkboxes/radios y el ítem de menú activo del backend. El "
        "texto de los botones se mantiene blanco (no se recalcula "
        "contraste) — elegí un color suficientemente oscuro.",
    )

    @api.constrains("cositt_backend_accent_color")
    def _check_cositt_backend_accent_color(self):
        for company in self:
            color = company.cositt_backend_accent_color
            if color and not COLOR_HEX_RE.match(color):
                raise ValidationError(_(
                    'Color de acento no válido: "%s". Usa el formato '
                    "hexadecimal #rrggbb (ej. #1a2b3c)."
                ) % color)

    def _cositt_get_backend_accent_color(self):
        """Hex string listo para inyectar en session_info() (ver
        models/ir_http.py), o False si no hay nada que aplicar —
        cubre tanto "desactivado" como "activado pero sin color
        elegido todavía", ambos casos visualmente neutros."""
        self.ensure_one()
        if not self.cositt_backend_accent_enabled:
            return False
        return self.cositt_backend_accent_color or False
