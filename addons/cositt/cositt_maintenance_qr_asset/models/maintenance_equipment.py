import base64
import io
import logging

import qrcode

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


def _sanitize_line(value):
    # Una línea física de la ficha por valor: un salto de línea suelto en
    # un campo de texto libre (p.ej. el nombre del equipo) no debe poder
    # inyectar una línea falsa adicional en el QR.
    if not value:
        return ""
    return " ".join(str(value).split())


def _build_equipment_card_text(
    name,
    category_name=None,
    model=None,
    serial_no=None,
    owner_name=None,
    technician_name=None,
    vendor_name=None,
    warranty_date=None,
):
    """Construye el texto plano de la ficha de identificación del activo,
    a partir de datos ya planos (sin recordset), para que sea una función
    pura y fácil de testear. No es un formato estándar (a diferencia de la
    vCard de contactos): no existe un equivalente para activos físicos, así
    que es simplemente texto legible línea a línea."""
    if not name:
        return ""

    lines = ["EQUIPO: %s" % _sanitize_line(name)]
    if category_name:
        lines.append("Categoría: %s" % _sanitize_line(category_name))
    if model:
        lines.append("Modelo: %s" % _sanitize_line(model))
    if serial_no:
        lines.append("Nº Serie: %s" % _sanitize_line(serial_no))
    if owner_name:
        lines.append("Propietario: %s" % _sanitize_line(owner_name))
    if technician_name:
        lines.append("Técnico: %s" % _sanitize_line(technician_name))
    if vendor_name:
        lines.append("Proveedor: %s" % _sanitize_line(vendor_name))
    if warranty_date:
        lines.append("Garantía hasta: %s" % _sanitize_line(warranty_date))

    return "\n".join(lines)


def _generate_qr_png(text):
    """Genera un PNG (bytes) del QR de la ficha. Nunca lanza: si algo falla
    en la generación, degrada a False para no romper la carga del
    formulario del activo (mismo criterio que cositt_contact_qr_vcard)."""
    if not text:
        return False
    try:
        image = qrcode.make(text, error_correction=qrcode.constants.ERROR_CORRECT_M)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception:
        _logger.warning("No se pudo generar el QR del activo", exc_info=True)
        return False


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    # No almacenado a propósito: el QR se recalcula con los datos vigentes
    # del activo en cada lectura. Pensado para el formulario (un registro a
    # la vez); no usar en listas/kanban/export masivo.
    qr_asset_card = fields.Binary(
        string="QR del activo",
        compute="_compute_qr_asset_card",
        store=False,
        help="Código QR generado localmente con la ficha del activo "
        "(nombre, categoría, modelo, nº de serie, propietario...). "
        "Escanéalo con la cámara de un móvil para leer la ficha "
        "directamente, sin necesitar conexión ni sesión en Odoo — "
        "pensado para imprimir en una etiqueta física.",
    )

    @api.depends(
        "name",
        "category_id.name",
        "model",
        "serial_no",
        "owner_user_id.name",
        "technician_user_id.name",
        "partner_id.name",
        "warranty_date",
    )
    def _compute_qr_asset_card(self):
        for equipment in self:
            try:
                card_text = _build_equipment_card_text(
                    name=equipment.name,
                    category_name=equipment.category_id.name,
                    model=equipment.model,
                    serial_no=equipment.serial_no,
                    owner_name=equipment.owner_user_id.name,
                    technician_name=equipment.technician_user_id.name,
                    vendor_name=equipment.partner_id.name,
                    warranty_date=equipment.warranty_date,
                )
                png_bytes = _generate_qr_png(card_text)
            except Exception:
                # No debe romper la carga del formulario del activo por un
                # problema puntual leyendo un campo relacionado (p.ej.
                # AccessError en un escenario multi-compañía) — degrada a
                # campo vacío, igual que cositt_contact_qr_vcard.
                _logger.warning(
                    "No se pudo generar el QR del activo %s (id=%s)",
                    equipment.display_name,
                    equipment.id,
                    exc_info=True,
                )
                png_bytes = False
            equipment.qr_asset_card = base64.b64encode(png_bytes) if png_bytes else False
