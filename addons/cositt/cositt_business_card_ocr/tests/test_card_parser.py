from odoo.tests.common import BaseCase

from ..models.card_parser import parse_card_text

SAMPLE_CARD = """
Juan Pérez García
Director Comercial
ACME Solutions S.L.
Calle Mayor 12, 28001 Madrid
Tel: 912 345 678
Móvil: 600 123 456
juan.perez@acme.com
www.acme.com
"""


class TestCardParser(BaseCase):
    def test_empty_text_returns_all_false(self):
        result = parse_card_text("")
        self.assertFalse(result["email"])
        self.assertFalse(result["partner_name"])

    def test_extracts_email(self):
        result = parse_card_text(SAMPLE_CARD)
        self.assertEqual(result["email"], "juan.perez@acme.com")

    def test_extracts_phone_and_mobile(self):
        result = parse_card_text(SAMPLE_CARD)
        self.assertEqual(result["phone"], "912 345 678")
        self.assertEqual(result["mobile"], "600 123 456")

    def test_extracts_website_even_if_domain_matches_email(self):
        result = parse_card_text(SAMPLE_CARD)
        self.assertTrue(result["website"])
        self.assertIn("acme.com", result["website"])

    def test_extracts_company_by_suffix(self):
        result = parse_card_text(SAMPLE_CARD)
        self.assertEqual(result["company_name"], "ACME Solutions S.L.")

    def test_extracts_job_title(self):
        result = parse_card_text(SAMPLE_CARD)
        self.assertEqual(result["function"], "Director Comercial")

    def test_extracts_name_as_first_free_line(self):
        result = parse_card_text(SAMPLE_CARD)
        self.assertEqual(result["partner_name"], "Juan Pérez García")

    def test_fax_lines_are_ignored_as_phone(self):
        text = "Fax: 911 111 111\njane@doe.com"
        result = parse_card_text(text)
        self.assertFalse(result["phone"])
        self.assertFalse(result["mobile"])

    def test_job_title_containing_sa_substring_is_not_mistaken_for_company(self):
        # Regresión: "responsable" contiene "sa" como subcadena ("respon-SA-ble"),
        # lo que antes hacía que se clasificara como sufijo societario.
        text = (
            "Carlos Fernandez Ruiz\n"
            "Responsable de Ventas\n"
            "Talleres Fernandez SL\n"
            "carlos@talleresfernandez.com"
        )
        result = parse_card_text(text)
        self.assertEqual(result["company_name"], "Talleres Fernandez SL")
        self.assertEqual(result["function"], "Responsable de Ventas")
        self.assertEqual(result["partner_name"], "Carlos Fernandez Ruiz")
        self.assertFalse(result["street"])
