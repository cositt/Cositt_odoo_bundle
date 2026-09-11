import base64
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

# 1x1 transparent PNG, just needs to be valid base64 for action_scan's decode step.
TINY_PNG_B64 = (
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    b"+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

SAMPLE_TEXT = (
    "Ana Ruiz\nGerente\nRuiz Consulting SL\n"
    "ana@ruizconsulting.com\nMóvil: 610 555 444"
)


class TestCositCardScan(TransactionCase):
    def _create_scan(self):
        return self.env["cositt.card.scan"].create(
            {
                "name": "Test scan",
                "image": TINY_PNG_B64,
                "image_filename": "card.png",
            }
        )

    def test_action_scan_requires_image(self):
        scan = self.env["cositt.card.scan"].create({"name": "No image"})
        with self.assertRaises(UserError):
            scan.action_scan()

    @patch("odoo.addons.cositt_business_card_ocr.models.ocr_provider.extract_text")
    def test_action_scan_parses_and_fills_fields(self, mock_extract):
        mock_extract.return_value = SAMPLE_TEXT
        scan = self._create_scan()
        scan.action_scan()

        self.assertEqual(scan.state, "scanned")
        self.assertEqual(scan.email, "ana@ruizconsulting.com")
        self.assertEqual(scan.mobile, "610 555 444")
        self.assertFalse(scan.duplicate_partner_id)

    @patch("odoo.addons.cositt_business_card_ocr.models.ocr_provider.extract_text")
    def test_action_scan_detects_duplicate_by_email(self, mock_extract):
        mock_extract.return_value = SAMPLE_TEXT
        existing = self.env["res.partner"].create(
            {"name": "Ana Ruiz (existente)", "email": "ana@ruizconsulting.com"}
        )
        scan = self._create_scan()
        scan.action_scan()

        self.assertEqual(scan.duplicate_partner_id, existing)

    @patch("odoo.addons.cositt_business_card_ocr.models.ocr_provider.extract_text")
    def test_action_confirm_creates_partner(self, mock_extract):
        mock_extract.return_value = SAMPLE_TEXT
        scan = self._create_scan()
        scan.action_scan()
        scan.action_confirm()

        self.assertEqual(scan.state, "done")
        self.assertTrue(scan.partner_id)
        self.assertEqual(scan.partner_id.name, "Ana Ruiz")
        self.assertEqual(scan.partner_id.email, "ana@ruizconsulting.com")
        self.assertEqual(scan.partner_id.phone, "610 555 444")
        self.assertEqual(scan.partner_id.company_name, "Ruiz Consulting SL")

    @patch("odoo.addons.cositt_business_card_ocr.models.ocr_provider.extract_text")
    def test_action_link_existing_does_not_create_new_partner(self, mock_extract):
        mock_extract.return_value = SAMPLE_TEXT
        existing = self.env["res.partner"].create(
            {"name": "Ana Ruiz (existente)", "email": "ana@ruizconsulting.com"}
        )
        partner_count_before = self.env["res.partner"].search_count([])

        scan = self._create_scan()
        scan.action_scan()
        scan.action_link_existing()

        self.assertEqual(scan.state, "done")
        self.assertEqual(scan.partner_id, existing)
        self.assertEqual(self.env["res.partner"].search_count([]), partner_count_before)

    def test_action_confirm_with_parent_creates_child_contact(self):
        company = self.env["res.partner"].create(
            {"name": "Ruiz Consulting SL", "is_company": True}
        )
        scan = self._create_scan()
        scan.write({"partner_name": "Ana Ruiz", "parent_partner_id": company.id})
        scan.write({"state": "scanned"})
        scan.action_confirm()

        self.assertEqual(scan.partner_id.parent_id, company)

    @patch("odoo.addons.cositt_business_card_ocr.models.ocr_provider.extract_text")
    def test_action_scan_detects_duplicate_by_email_case_insensitive(self, mock_extract):
        mock_extract.return_value = SAMPLE_TEXT  # email: ana@ruizconsulting.com
        existing = self.env["res.partner"].create(
            {"name": "Ana Ruiz (existente)", "email": "ANA@RuizConsulting.COM"}
        )
        scan = self._create_scan()
        scan.action_scan()

        self.assertEqual(scan.duplicate_partner_id, existing)

    @patch("odoo.addons.cositt_business_card_ocr.models.ocr_provider.extract_text")
    def test_action_scan_detects_duplicate_by_phone_regardless_of_format(
        self, mock_extract
    ):
        mock_extract.return_value = "Ana Ruiz\nTel: 610-555-444"
        existing = self.env["res.partner"].create(
            {"name": "Ana Ruiz (existente)", "phone": "+34 610 555 444"}
        )
        scan = self._create_scan()
        scan.action_scan()

        self.assertEqual(scan.duplicate_partner_id, existing)

    def test_action_discard_sets_state(self):
        scan = self._create_scan()
        scan.action_discard()
        self.assertEqual(scan.state, "discarded")

    @patch("odoo.addons.cositt_business_card_ocr.models.ocr_provider.extract_text")
    def test_action_confirm_twice_is_blocked(self, mock_extract):
        mock_extract.return_value = SAMPLE_TEXT
        scan = self._create_scan()
        scan.action_scan()
        scan.action_confirm()

        with self.assertRaises(UserError):
            scan.action_confirm()

    @patch("odoo.addons.cositt_business_card_ocr.models.ocr_provider.extract_text")
    def test_action_link_existing_twice_is_blocked(self, mock_extract):
        mock_extract.return_value = SAMPLE_TEXT
        self.env["res.partner"].create(
            {"name": "Ana Ruiz (existente)", "email": "ana@ruizconsulting.com"}
        )
        scan = self._create_scan()
        scan.action_scan()
        scan.action_link_existing()

        with self.assertRaises(UserError):
            scan.action_link_existing()

    @patch("odoo.addons.cositt_business_card_ocr.models.ocr_provider.extract_text")
    def test_action_scan_wraps_ocr_failure_as_user_error(self, mock_extract):
        mock_extract.side_effect = RuntimeError("tesseract no disponible")
        scan = self._create_scan()

        with self.assertRaises(UserError):
            scan.action_scan()
        self.assertEqual(scan.state, "draft")
