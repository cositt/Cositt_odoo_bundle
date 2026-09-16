import base64
from unittest.mock import patch

from odoo.tests.common import BaseCase, TransactionCase

from ..models import maintenance_equipment
from ..models.maintenance_equipment import (
    _build_equipment_card_text,
    _generate_qr_png,
    _sanitize_line,
)

PNG_MAGIC = b"\x89PNG"


class TestSanitizeLine(BaseCase):
    """Función pura, sin ORM — mismo criterio que los demás plugins: no
    confiar en que el texto libre de un campo (p.ej. el nombre del
    equipo) no contenga un salto de línea que inyecte una línea falsa
    adicional en la ficha."""

    def test_collapses_internal_newline_to_space(self):
        self.assertEqual(_sanitize_line("Linea1\nLinea2"), "Linea1 Linea2")

    def test_collapses_multiple_whitespace(self):
        self.assertEqual(_sanitize_line("  a   b  "), "a b")

    def test_empty_value_returns_empty_string(self):
        self.assertEqual(_sanitize_line(False), "")
        self.assertEqual(_sanitize_line(None), "")
        self.assertEqual(_sanitize_line(""), "")


class TestBuildEquipmentCardText(BaseCase):
    def test_no_name_returns_empty(self):
        self.assertEqual(_build_equipment_card_text(name=False), "")

    def test_minimal_only_name(self):
        text = _build_equipment_card_text(name="Router principal")
        self.assertEqual(text, "EQUIPO: Router principal")

    def test_optional_fields_included_when_present(self):
        text = _build_equipment_card_text(
            name="Impresora 3D",
            category_name="Electrónica",
            model="Prusa MK4",
            serial_no="SN-001",
            owner_name="Ana Torres",
            technician_name="Pedro Sánchez",
            vendor_name="Proveedor SL",
            warranty_date="2027-01-01",
        )
        self.assertIn("EQUIPO: Impresora 3D", text)
        self.assertIn("Categoría: Electrónica", text)
        self.assertIn("Modelo: Prusa MK4", text)
        self.assertIn("Nº Serie: SN-001", text)
        self.assertIn("Propietario: Ana Torres", text)
        self.assertIn("Técnico: Pedro Sánchez", text)
        self.assertIn("Proveedor: Proveedor SL", text)
        self.assertIn("Garantía hasta: 2027-01-01", text)

    def test_optional_fields_omitted_when_missing(self):
        text = _build_equipment_card_text(name="Solo Nombre")
        self.assertNotIn("Categoría:", text)
        self.assertNotIn("Modelo:", text)
        self.assertNotIn("Nº Serie:", text)
        self.assertNotIn("Propietario:", text)
        self.assertNotIn("Técnico:", text)
        self.assertNotIn("Proveedor:", text)
        self.assertNotIn("Garantía hasta:", text)

    def test_free_text_field_cannot_inject_extra_line(self):
        text = _build_equipment_card_text(
            name="Router\nGarantía hasta: 2099-01-01"
        )
        # Debe quedar en UNA sola línea "EQUIPO: ...", no crear una
        # segunda línea "Garantía hasta: ..." falsa.
        self.assertEqual(text, "EQUIPO: Router Garantía hasta: 2099-01-01")
        self.assertEqual(text.count("\n"), 0)


class TestGenerateQrPng(BaseCase):
    def test_generates_valid_png_bytes(self):
        png_bytes = _generate_qr_png("EQUIPO: Router principal")
        self.assertTrue(png_bytes.startswith(PNG_MAGIC))

    def test_empty_text_returns_false(self):
        self.assertFalse(_generate_qr_png(""))
        self.assertFalse(_generate_qr_png(False))

    def test_qrcode_failure_degrades_to_false(self):
        with patch("qrcode.make", side_effect=RuntimeError("boom")):
            self.assertFalse(_generate_qr_png("EQUIPO: X"))


class TestMaintenanceEquipmentQrField(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Reutiliza el usuario admin ya existente en vez de crear uno
        # nuevo: res.users.create() falla en este entorno bajo
        # --test-enable por un problema de entorno ajeno a este módulo
        # (ver memoria de sesión / cositt_pdf_merge).
        cls.admin = cls.env.ref("base.user_admin")

    def test_field_populated_with_minimal_data(self):
        equipment = self.env["maintenance.equipment"].create(
            {"name": "Router de prueba"}
        )
        self.assertTrue(equipment.qr_asset_card)
        self.assertTrue(base64_starts_with_png(equipment.qr_asset_card))

    def test_field_populated_with_full_data(self):
        category = self.env["maintenance.equipment.category"].create(
            {"name": "Categoría de Prueba"}
        )
        equipment = self.env["maintenance.equipment"].create({
            "name": "Impresora de prueba",
            "category_id": category.id,
            "model": "Modelo X",
            "serial_no": "SN-TEST-001",
            "owner_user_id": self.admin.id,
        })
        self.assertTrue(equipment.qr_asset_card)

    def test_field_recomputes_when_name_changes(self):
        equipment = self.env["maintenance.equipment"].create(
            {"name": "Nombre Original"}
        )
        first_qr = equipment.qr_asset_card
        equipment.name = "Nombre Cambiado"
        self.assertNotEqual(equipment.qr_asset_card, first_qr)

    def test_field_recomputes_when_serial_no_changes(self):
        equipment = self.env["maintenance.equipment"].create(
            {"name": "Con Nº Serie", "serial_no": "SN-A"}
        )
        first_qr = equipment.qr_asset_card
        equipment.serial_no = "SN-B"
        self.assertNotEqual(equipment.qr_asset_card, first_qr)

    def test_field_is_not_stored(self):
        field = self.env["maintenance.equipment"]._fields["qr_asset_card"]
        self.assertFalse(field.store)

    def test_compute_survives_build_card_text_exception(self):
        # Mismo criterio que cositt_contact_qr_vcard: un fallo puntual
        # generando la ficha no debe romper la carga del formulario del
        # activo, solo dejar el campo vacío.
        equipment = self.env["maintenance.equipment"].create(
            {"name": "Con Fallo"}
        )
        with patch.object(
            maintenance_equipment,
            "_build_equipment_card_text",
            side_effect=RuntimeError("boom"),
        ):
            equipment.invalidate_recordset(["qr_asset_card"])
            self.assertFalse(equipment.qr_asset_card)


def base64_starts_with_png(value):
    return base64.b64decode(value).startswith(PNG_MAGIC)
