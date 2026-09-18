from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

MESSAGE_MAX_LENGTH = 300


class ResCompany(models.Model):
    _inherit = "res.company"

    cositt_announcement_banner_enabled = fields.Boolean(
        string="Aviso activo",
        default=False,
        help="Mientras esté desactivado, el backend se ve exactamente "
        "igual que sin este módulo instalado.",
    )
    cositt_announcement_banner_message = fields.Char(
        string="Mensaje del aviso",
        help="Se muestra en una barra fija en la parte superior del "
        "backend, a todos los usuarios internos de esta compañía, "
        "hasta que lo cierren (por sesión de navegador).",
    )
    cositt_announcement_banner_style = fields.Selection(
        [
            ("info", "Info"),
            ("success", "Éxito"),
            ("warning", "Aviso"),
            ("danger", "Urgente"),
        ],
        string="Estilo del aviso",
        default="info",
    )

    @api.constrains("cositt_announcement_banner_message")
    def _check_cositt_announcement_banner_message(self):
        for company in self:
            message = company.cositt_announcement_banner_message
            if message and len(message) > MESSAGE_MAX_LENGTH:
                raise ValidationError(_(
                    "El mensaje del aviso es demasiado largo (máximo "
                    "%(max)s caracteres, tiene %(got)s)."
                ) % {"max": MESSAGE_MAX_LENGTH, "got": len(message)})

    def _cositt_get_announcement_banner_config(self):
        """Dict listo para inyectar en session_info() (ver
        models/ir_http.py), o False si no hay nada que mostrar — cubre
        tanto "desactivado" como "activado pero sin mensaje todavía",
        ambos casos visualmente neutros."""
        self.ensure_one()
        message = (self.cositt_announcement_banner_message or "").strip()
        if not self.cositt_announcement_banner_enabled or not message:
            return False
        return {
            "message": message,
            "style": self.cositt_announcement_banner_style,
        }
