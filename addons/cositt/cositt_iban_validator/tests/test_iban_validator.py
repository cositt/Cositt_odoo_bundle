from odoo.exceptions import ValidationError
from odoo.tests.common import BaseCase, TransactionCase

from ..models.iban_validator import check_iban, looks_like_iban

VALID_GB = "GB82 WEST 1234 5698 7654 32"
VALID_DE = "DE89 3704 0044 0532 0130 00"
VALID_ES = "ES91 2100 0418 4502 0005 1332"


class TestIbanValidatorPure(BaseCase):
    def test_valid_ibans_pass(self):
        for value in (VALID_GB, VALID_DE, VALID_ES):
            self.assertIsNone(check_iban(value), value)

    def test_lowercase_and_spaces_are_normalized(self):
        self.assertIsNone(check_iban(VALID_ES.lower()))

    def test_invalid_checksum_fails(self):
        broken = VALID_GB[:-1] + str((int(VALID_GB[-1]) + 1) % 10)
        self.assertIsNotNone(check_iban(broken))

    def test_wrong_length_for_country_fails(self):
        too_short = VALID_ES.replace(" ", "")[:-1]  # 23 en vez de 24
        error = check_iban(too_short)
        self.assertIsNotNone(error)
        self.assertIn("ES", error)

    def test_bad_format_fails(self):
        self.assertIsNotNone(check_iban("ESXX INVALID IBAN"))

    def test_looks_like_iban(self):
        self.assertTrue(looks_like_iban(VALID_ES))
        self.assertFalse(looks_like_iban("123456789"))
        self.assertFalse(looks_like_iban(""))
        self.assertFalse(looks_like_iban(False))

    def test_rejects_unicode_digits_in_check_digits(self):
        # Regresión: \d sin re.ASCII acepta dígitos Unicode no-ASCII
        # (p.ej. arábigo-índicos), que int(ch, 36) normaliza en silencio,
        # colando un IBAN con caracteres inválidos como si fuera correcto.
        unicode_digits = VALID_ES.replace(" ", "").replace("91", "٩١", 1)
        self.assertIsNotNone(check_iban(unicode_digits))

    def test_country_not_in_length_table_uses_checksum_only(self):
        # Un país IBAN no incluido en la tabla (aquí "XX", sintético) debe
        # validarse solo por formato y dígito de control, sin exigir una
        # longitud exacta. Se busca por fuerza bruta (100 combinaciones,
        # trivial) un par de dígitos de control que dé un checksum válido.
        from ..models.iban_validator import IBAN_LENGTHS, _mod97

        self.assertNotIn("XX", IBAN_LENGTHS)
        bban = "0" * 16
        for check in range(100):
            candidate = "XX%02d%s" % (check, bban)
            if _mod97(candidate) == 1:
                self.assertIsNone(check_iban(candidate))
                break
        else:
            self.fail("no se encontró un dígito de control válido de prueba")

    def test_boundary_lengths(self):
        too_short = "AA00" + "A" * 10  # 14 caracteres, por debajo de 15
        self.assertIsNotNone(check_iban(too_short))
        too_long = "AA00" + "A" * 31  # 35 caracteres, por encima de 34
        self.assertIsNotNone(check_iban(too_long))


class TestIbanValidatorPartnerBank(TransactionCase):
    def _partner(self):
        return self.env["res.partner"].create({"name": "Cliente IBAN"})

    def test_valid_iban_is_accepted(self):
        bank = self.env["res.partner.bank"].create(
            {"acc_number": VALID_ES, "partner_id": self._partner().id}
        )
        self.assertTrue(bank.exists())

    def test_invalid_checksum_is_rejected(self):
        broken = VALID_ES.replace(" ", "")[:-1] + "0"
        with self.assertRaises(ValidationError):
            self.env["res.partner.bank"].create(
                {"acc_number": broken, "partner_id": self._partner().id}
            )

    def test_write_to_invalid_iban_is_rejected(self):
        # @api.constrains debe dispararse también al modificar una cuenta
        # ya guardada con un número válido, no solo al crearla.
        bank = self.env["res.partner.bank"].create(
            {"acc_number": VALID_ES, "partner_id": self._partner().id}
        )
        broken = VALID_ES.replace(" ", "")[:-1] + "0"
        with self.assertRaises(ValidationError):
            bank.write({"acc_number": broken})

    def test_non_iban_account_number_is_not_validated(self):
        # Números de cuenta que no tienen forma de IBAN (muchos países no
        # usan IBAN) no deben forzarse a este formato.
        bank = self.env["res.partner.bank"].create(
            {"acc_number": "123456789", "partner_id": self._partner().id}
        )
        self.assertTrue(bank.exists())
