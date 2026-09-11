from odoo.exceptions import UserError
from odoo.tests.common import BaseCase, TransactionCase

from ..models.res_partner import _extract_single_phone_digits


class TestExtractSinglePhoneDigits(BaseCase):
    """Pruebas puras del respaldo (sin ORM, sin depender de si la librería
    de validación de teléfonos logra sanitizar o no un valor dado, que
    resultó ser más permisiva de lo esperado en varios casos probados a
    mano contra la instancia real)."""

    def test_strips_non_digits(self):
        self.assertEqual(_extract_single_phone_digits("611-222-333"), "611222333")

    def test_strips_00_international_prefix(self):
        self.assertEqual(
            _extract_single_phone_digits("0034611222333"), "34611222333"
        )

    def test_returns_none_for_multiple_numbers(self):
        self.assertIsNone(
            _extract_single_phone_digits("91 123 45 67 / 611 222 333")
        )

    def test_returns_none_for_extension(self):
        self.assertIsNone(_extract_single_phone_digits("611 222 333 ext 45"))


class TestQuickWhatsapp(TransactionCase):
    def test_opens_whatsapp_with_sanitized_number(self):
        partner = self.env["res.partner"].create(
            {"name": "Con Prefijo", "phone": "+34 600 111 222"}
        )
        action = partner.action_open_whatsapp()

        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(action["url"], "https://wa.me/34600111222")
        self.assertEqual(action["target"], "new")

    def test_opens_whatsapp_with_00_prefix(self):
        # "00" como prefijo de salida internacional lo reconoce ya la
        # propia librería de validación de Odoo (phone_sanitized no queda
        # en False aquí), así que este es un camino normal, no el respaldo.
        partner = self.env["res.partner"].create(
            {"name": "Prefijo 00", "phone": "0034611222333"}
        )
        action = partner.action_open_whatsapp()
        self.assertEqual(action["url"], "https://wa.me/34611222333")

    def test_falls_back_to_raw_digits_when_not_sanitizable(self):
        # "1111111111" tiene dígitos pero no es un número válido para la
        # librería de validación (verificado a mano, sea cual sea el país
        # de la compañía), así que phone_sanitized queda en False y se usa
        # el respaldo: quitar todo lo que no sea dígito del valor tal cual.
        partner = self.env["res.partner"].create(
            {"name": "Numero Invalido Con Digitos", "phone": "1111111111"}
        )
        self.assertFalse(partner.phone_sanitized)

        action = partner.action_open_whatsapp()
        self.assertEqual(action["url"], "https://wa.me/1111111111")

    def test_requires_phone(self):
        partner = self.env["res.partner"].create({"name": "Sin Telefono"})
        with self.assertRaises(UserError):
            partner.action_open_whatsapp()

    def test_rejects_phone_without_digits(self):
        partner = self.env["res.partner"].create(
            {"name": "Telefono Invalido", "phone": "n/a"}
        )
        with self.assertRaises(UserError):
            partner.action_open_whatsapp()

    def test_rejects_multiple_phone_numbers(self):
        # No es un número válido para la librería (verificado a mano), así
        # que cae en el respaldo, que detecta el "/" y no sabe cuál usar.
        partner = self.env["res.partner"].create(
            {"name": "Dos Telefonos", "phone": "91 123 45 67 / 611 222 333"}
        )
        self.assertFalse(partner.phone_sanitized)
        with self.assertRaises(UserError):
            partner.action_open_whatsapp()

    def test_rejects_too_short_fallback_number(self):
        partner = self.env["res.partner"].create(
            {"name": "Numero Corto", "phone": "123"}
        )
        with self.assertRaises(UserError):
            partner.action_open_whatsapp()

    def test_view_extension_is_installed(self):
        view = self.env.ref(
            "cositt_quick_whatsapp.view_partner_form_inherit_whatsapp"
        )
        self.assertEqual(view.inherit_id, self.env.ref("base.view_partner_form"))

    def test_button_is_placed_in_header_not_child_contacts_template(self):
        # Regresión: el botón debe quedar anclado a la cabecera principal
        # (nombre/email/teléfono), no a la plantilla de contactos hijos que
        # vive dentro del <notebook> más abajo en la misma vista base.
        view = self.env["res.partner"].get_view(
            view_id=self.env.ref("base.view_partner_form").id, view_type="form"
        )
        arch = view["arch"]

        self.assertEqual(arch.count("action_open_whatsapp"), 1)
        button_pos = arch.index("action_open_whatsapp")
        notebook_pos = arch.index("<notebook")
        self.assertLess(button_pos, notebook_pos)
