from unittest.mock import patch

from odoo.tests.common import BaseCase, TransactionCase

from ..models import res_partner
from ..models.res_partner import _build_vcard_text, _generate_qr_png, _vcard_escape

PNG_MAGIC = b"\x89PNG"


class TestVcardEscape(BaseCase):
    """Escapado RFC 6350, probado aislado (sin ORM) — mismo patrón que el
    plugin de WhatsApp: no confiar en librerías externas sin verificarlo."""

    def test_escapes_semicolon(self):
        self.assertEqual(_vcard_escape("Perez; Sanchez"), "Perez\\; Sanchez")

    def test_escapes_comma(self):
        self.assertEqual(_vcard_escape("Responsable, Ventas"), "Responsable\\, Ventas")

    def test_escapes_backslash_before_other_chars(self):
        # El backslash debe escaparse primero para no dañar los escapes
        # que se añaden después (";" y ",").
        self.assertEqual(_vcard_escape("C:\\ruta;x"), "C:\\\\ruta\\;x")

    def test_escapes_newline(self):
        self.assertEqual(_vcard_escape("Linea1\nLinea2"), "Linea1\\nLinea2")

    def test_escapes_crlf_as_single_newline(self):
        self.assertEqual(_vcard_escape("Linea1\r\nLinea2"), "Linea1\\nLinea2")

    def test_escapes_lone_cr_as_newline(self):
        # Un "\r" suelto (sin "\n" detrás) no debe quedar como carácter de
        # control real: varios lectores de vCard lo tratan igual que un
        # salto de línea, lo que permitiría inyectar una propiedad falsa
        # (p.ej. otro TEL/EMAIL) a través de un campo de texto libre.
        self.assertEqual(_vcard_escape("Linea1\rLinea2"), "Linea1\\nLinea2")

    def test_empty_value_returns_empty_string(self):
        self.assertEqual(_vcard_escape(False), "")
        self.assertEqual(_vcard_escape(None), "")
        self.assertEqual(_vcard_escape(""), "")


class TestBuildVcardText(BaseCase):
    """Construcción de la vCard como función pura — sin tocar la base de
    datos, para poder cubrir combinaciones de campos rápido."""

    def test_individual_basic_has_fn_and_n(self):
        text = _build_vcard_text(name="Pedro Sanchez", is_company=False)
        self.assertIn("BEGIN:VCARD", text)
        self.assertIn("VERSION:3.0", text)
        self.assertIn("FN:Pedro Sanchez", text)
        self.assertIn("N:;Pedro Sanchez;;;", text)
        self.assertIn("END:VCARD", text)

    def test_company_uses_org_not_n(self):
        text = _build_vcard_text(name="Innova Digital SL", is_company=True)
        self.assertIn("FN:Innova Digital SL", text)
        self.assertIn("ORG:Innova Digital SL", text)
        self.assertNotIn("N:;Innova Digital SL;;;", text)

    def test_no_name_returns_empty(self):
        self.assertEqual(_build_vcard_text(name=False, is_company=False), "")
        self.assertEqual(_build_vcard_text(name=None, is_company=False), "")

    def test_optional_fields_omitted_when_missing(self):
        text = _build_vcard_text(name="Sin Datos", is_company=False)
        self.assertNotIn("TEL", text)
        self.assertNotIn("EMAIL", text)
        self.assertNotIn("ADR", text)
        self.assertNotIn("URL", text)
        self.assertNotIn("TITLE", text)

    def test_phone_uses_unified_phone_field(self):
        # Odoo 19 unificó "mobile" dentro de "phone" en res.partner — no
        # existe un campo mobile separado (ver notas de plugins previos).
        text = _build_vcard_text(name="Con Telefono", is_company=False, phone="611222333")
        self.assertIn("TEL;TYPE=WORK,VOICE:611222333", text)

    def test_email_included_when_present(self):
        text = _build_vcard_text(name="Con Email", is_company=False, email="a@b.com")
        self.assertIn("EMAIL;TYPE=INTERNET:a@b.com", text)

    def test_title_and_company_name_for_individual(self):
        # company_name viene de commercial_company_name en el modelo, que
        # cubre tanto el caso de empresa vinculada por parent_id como el de
        # una empresa indicada como texto libre sin registro propio.
        text = _build_vcard_text(
            name="Empleado",
            is_company=False,
            function="Responsable de Ventas",
            company_name="Innova Digital SL",
        )
        self.assertIn("TITLE:Responsable de Ventas", text)
        self.assertIn("ORG:Innova Digital SL", text)

    def test_address_included_when_street_present(self):
        text = _build_vcard_text(
            name="Con Direccion",
            is_company=False,
            street="Calle Mayor 1",
            city="Madrid",
            zip_code="28001",
            country_name="Spain",
        )
        self.assertIn("ADR;TYPE=WORK:;;Calle Mayor 1;Madrid;;28001;Spain", text)

    def test_address_includes_street2_as_extended_address(self):
        text = _build_vcard_text(
            name="Con Direccion Extendida",
            is_company=False,
            street="Calle Mayor 1",
            street2="3izda",
            city="Madrid",
        )
        self.assertIn("ADR;TYPE=WORK:;3izda;Calle Mayor 1;Madrid;;;", text)

    def test_address_included_when_only_city_present(self):
        # Regresión: antes se exigía "street" para incluir ADR, y se perdía
        # la ciudad/país cuando solo faltaba la calle.
        text = _build_vcard_text(
            name="Solo Ciudad", is_company=False, city="Madrid", country_name="Spain"
        )
        self.assertIn("ADR;TYPE=WORK:;;;Madrid;;;Spain", text)

    def test_website_included_when_present(self):
        text = _build_vcard_text(
            name="Con Web", is_company=True, website="https://cositt.com"
        )
        self.assertIn("URL:https://cositt.com", text)

    def test_special_characters_are_escaped_in_output(self):
        text = _build_vcard_text(name="Perez; Sanchez, Juan", is_company=False)
        self.assertIn("FN:Perez\\; Sanchez\\, Juan", text)

    def test_uses_crlf_line_endings(self):
        text = _build_vcard_text(name="Con CRLF", is_company=False)
        self.assertIn("\r\n", text)


class TestGenerateQrPng(BaseCase):
    def test_generates_valid_png_bytes(self):
        png_bytes = _generate_qr_png("BEGIN:VCARD\r\nVERSION:3.0\r\nFN:X\r\nEND:VCARD\r\n")
        self.assertTrue(png_bytes.startswith(PNG_MAGIC))

    def test_empty_text_returns_false(self):
        self.assertFalse(_generate_qr_png(""))
        self.assertFalse(_generate_qr_png(False))

    def test_qrcode_failure_degrades_to_false(self):
        with patch("qrcode.make", side_effect=RuntimeError("boom")):
            self.assertFalse(_generate_qr_png("BEGIN:VCARD\r\nEND:VCARD\r\n"))


class TestResPartnerQrVcardField(TransactionCase):
    def test_field_populated_for_individual_with_data(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Pedro Sanchez",
                "email": "pedro@example.com",
                "phone": "611222333",
            }
        )
        self.assertTrue(partner.qr_vcard)
        self.assertTrue(base64_starts_with_png(partner.qr_vcard))

    def test_field_populated_for_company(self):
        partner = self.env["res.partner"].create(
            {"name": "Innova Digital SL", "is_company": True}
        )
        self.assertTrue(partner.qr_vcard)

    def test_field_recomputes_when_name_changes(self):
        partner = self.env["res.partner"].create({"name": "Nombre Original"})
        first_qr = partner.qr_vcard
        partner.name = "Nombre Cambiado"
        self.assertNotEqual(partner.qr_vcard, first_qr)

    def test_field_is_not_stored(self):
        field = self.env["res.partner"]._fields["qr_vcard"]
        self.assertFalse(field.store)

    def test_field_recomputes_when_commercial_company_changes(self):
        # Cubre el cambio de dependencia de parent_id.name a
        # commercial_company_name tras el fix del review.
        partner = self.env["res.partner"].create({"name": "Empleado Suelto"})
        qr_before = partner.qr_vcard
        company = self.env["res.partner"].create(
            {"name": "Empresa Nueva", "is_company": True}
        )
        partner.parent_id = company
        self.assertNotEqual(partner.qr_vcard, qr_before)

    def test_compute_survives_build_vcard_exception(self):
        # Regresión HIGH del review: antes solo _generate_qr_png estaba
        # protegido; un fallo leyendo campos relacionados (country_id,
        # commercial_company_name) rompía la carga del formulario entero.
        partner = self.env["res.partner"].create({"name": "Con Fallo"})
        with patch.object(
            res_partner, "_build_vcard_text", side_effect=RuntimeError("boom")
        ):
            partner.invalidate_recordset(["qr_vcard"])
            self.assertFalse(partner.qr_vcard)


def base64_starts_with_png(value):
    import base64

    return base64.b64decode(value).startswith(PNG_MAGIC)
