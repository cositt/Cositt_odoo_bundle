from odoo import _, api, models
from odoo.exceptions import ValidationError

from .iban_validator import check_iban, looks_like_iban


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    @api.constrains("acc_number")
    def _check_cositt_iban(self):
        for bank in self:
            if not looks_like_iban(bank.acc_number):
                # No parece un IBAN (muchos países no lo usan): no se
                # fuerza el formato IBAN a cuentas que no lo son.
                continue
            error = check_iban(bank.acc_number)
            if error:
                raise ValidationError(
                    _('"%s" no parece una cuenta IBAN válida: %s')
                    % (bank.acc_number, error)
                )
