from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

LABEL_MAX_LENGTH = 140

# Las claves de THEME_KINDS deben coincidir con las de SEASONAL_THEMES en
# static/src/seasonal_theme/theme_data.js (icono/color/partículas por
# tema) — si se agrega un tema aquí sin su entrada equivalente en JS,
# getSeasonalTheme() cae en silencio a "christmas" en vez de fallar.
THEME_KINDS = [
    ("christmas", "Navidad"),
    ("fair", "Feria"),
    ("birthday", "Cumpleaños"),
    ("custom", "Campaña personalizada"),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    cositt_seasonal_theme_enabled = fields.Boolean(
        string="Decoración activa",
        default=False,
        help="Mientras esté desactivada, el backend se ve exactamente "
        "igual que sin este módulo instalado.",
    )
    cositt_seasonal_theme_kind = fields.Selection(
        THEME_KINDS,
        string="Tema",
        default="christmas",
        help="Determina el icono de la barra de navegación y el tipo de "
        "partículas decorativas (copos, flores, velas...).",
    )
    cositt_seasonal_theme_label = fields.Char(
        string="Mensaje",
        help="Texto opcional mostrado al pasar el ratón por el icono de "
        "la barra de navegación. Si se deja vacío, se usa un mensaje "
        "genérico según el tema elegido.",
    )
    cositt_seasonal_theme_animation_enabled = fields.Boolean(
        string="Partículas animadas",
        default=True,
        help="Copos, flores u otras partículas decorativas flotando "
        "sobre el backend. Desactivar deja solo el icono de la barra de "
        "navegación, sin animación.",
    )
    cositt_seasonal_theme_date_start = fields.Date(
        string="Desde",
        help="Si se deja vacío, la decoración está activa desde ya "
        "(mientras el interruptor de arriba siga encendido).",
    )
    cositt_seasonal_theme_date_end = fields.Date(
        string="Hasta",
        help="Si se deja vacío, la decoración no tiene fecha de fin "
        "automática.",
    )

    @api.constrains("cositt_seasonal_theme_date_start", "cositt_seasonal_theme_date_end")
    def _check_cositt_seasonal_theme_dates(self):
        for company in self:
            start = company.cositt_seasonal_theme_date_start
            end = company.cositt_seasonal_theme_date_end
            if start and end and end < start:
                raise ValidationError(_(
                    'La fecha "Hasta" (%(end)s) no puede ser anterior a "Desde" (%(start)s).'
                ) % {"end": end, "start": start})

    @api.constrains("cositt_seasonal_theme_label")
    def _check_cositt_seasonal_theme_label(self):
        for company in self:
            label = company.cositt_seasonal_theme_label
            if label and len(label) > LABEL_MAX_LENGTH:
                raise ValidationError(_(
                    "El mensaje es demasiado largo (máximo %(max)s "
                    "caracteres, tiene %(got)s)."
                ) % {"max": LABEL_MAX_LENGTH, "got": len(label)})

    def _cositt_get_seasonal_theme_config(self):
        """Dict listo para inyectar en session_info() (ver
        models/ir_http.py), o False si no hay nada que mostrar — cubre
        "desactivado" y "fuera del rango de fechas configurado"."""
        self.ensure_one()
        if not self.cositt_seasonal_theme_enabled:
            return False
        today = fields.Date.context_today(self)
        if self.cositt_seasonal_theme_date_start and today < self.cositt_seasonal_theme_date_start:
            return False
        if self.cositt_seasonal_theme_date_end and today > self.cositt_seasonal_theme_date_end:
            return False
        return {
            "kind": self.cositt_seasonal_theme_kind,
            "label": self.cositt_seasonal_theme_label or False,
            "animation_enabled": self.cositt_seasonal_theme_animation_enabled,
        }
