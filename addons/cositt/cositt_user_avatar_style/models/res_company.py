import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

HEX_COLOR_RE = re.compile(r"\A#[0-9A-Fa-f]{6}\Z")


class ResCompany(models.Model):
    _inherit = "res.company"

    cositt_avatar_style_enabled = fields.Boolean(
        string="Paleta de marca para avatares",
        default=False,
        help="Mientras esté desactivado, los avatares generados "
        "automáticamente (contactos, empleados... cualquier registro "
        "sin foto) se ven exactamente igual que sin este módulo "
        "instalado: color aleatorio elegido por Odoo.",
    )
    cositt_avatar_style_palette = fields.Char(
        string="Colores de marca",
        default="#714b67",
        help="Uno o más colores hexadecimales (#rrggbb) separados por "
        "coma. Cada persona sin foto obtiene siempre el mismo color de "
        "esta lista (elegido de forma determinista por su nombre), en "
        "vez del color aleatorio que usa Odoo por defecto — mismo "
        "aspecto para toda la organización.",
    )

    @api.constrains("cositt_avatar_style_enabled", "cositt_avatar_style_palette")
    def _check_cositt_avatar_style_palette(self):
        for company in self:
            if not company.cositt_avatar_style_enabled:
                continue
            tokens = [
                token.strip()
                for token in (company.cositt_avatar_style_palette or "").split(",")
                if token.strip()
            ]
            if not tokens:
                raise ValidationError(_(
                    "Agregá al menos un color hexadecimal (#rrggbb) a "
                    "la paleta de marca."
                ))
            for token in tokens:
                if not HEX_COLOR_RE.match(token):
                    raise ValidationError(_(
                        'Color de marca no válido: "%s". Usa el formato '
                        "hexadecimal #rrggbb (ej. #1a2b3c), separando "
                        "varios colores con comas."
                    ) % token)

    def _cositt_get_avatar_palette(self):
        """Lista de colores hex válidos, o [] si la paleta de marca está
        desactivada — cubre tanto "desactivado" como "activado pero sin
        paleta todavía" (aunque el segundo caso ya lo bloquea el
        constrains de arriba, se mantiene el mismo criterio defensivo
        que el resto de módulos del proyecto)."""
        self.ensure_one()
        if not self.cositt_avatar_style_enabled:
            return []
        return [
            token.strip()
            for token in (self.cositt_avatar_style_palette or "").split(",")
            if token.strip()
        ]
