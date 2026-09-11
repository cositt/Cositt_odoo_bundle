import re

from odoo import _, models
from odoo.exceptions import UserError

# Rango de longitud de un número E.164 completo (código de país + número).
MIN_PHONE_DIGITS = 8
MAX_PHONE_DIGITS = 15
# Indicios de que el campo contiene más de un teléfono o una extensión
# (p. ej. "91 123 45 67 / 611 222 333", "611 222 333 ext 45"): en esos
# casos no se puede extraer un único número de forma fiable.
MULTIPLE_OR_EXTENSION_RE = re.compile(r"[/,;]|\bext\b|\bx\d", re.IGNORECASE)


def _extract_single_phone_digits(raw_phone):
    """Dígitos de un único teléfono, para cuando Odoo no pudo normalizarlo
    (phone_sanitized es False: sin país configurado en la compañía y sin
    prefijo +CC en el número). Devuelve None si el texto sugiere varios
    teléfonos o una extensión, para que el llamante avise con un error en
    vez de construir un enlace wa.me incorrecto en silencio.
    """
    if MULTIPLE_OR_EXTENSION_RE.search(raw_phone):
        return None
    digits = re.sub(r"[^0-9]", "", raw_phone)
    if digits.startswith("00"):
        # Prefijo de salida internacional (España y la mayoría de Europa)
        # equivale a "+", que wa.me no necesita.
        digits = digits[2:]
    return digits


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_open_whatsapp(self):
        self.ensure_one()
        if not self.phone:
            raise UserError(_("Este contacto no tiene teléfono."))

        if self.phone_sanitized:
            number = self.phone_sanitized.lstrip("+")
        else:
            number = _extract_single_phone_digits(self.phone)

        if not number or not (MIN_PHONE_DIGITS <= len(number) <= MAX_PHONE_DIGITS):
            raise UserError(
                _(
                    'El teléfono de este contacto ("%s") no parece un número '
                    "completo y válido. Corrígelo antes de abrir WhatsApp."
                )
                % self.phone
            )

        return {
            "type": "ir.actions.act_url",
            "url": "https://wa.me/%s" % number,
            "target": "new",
        }
