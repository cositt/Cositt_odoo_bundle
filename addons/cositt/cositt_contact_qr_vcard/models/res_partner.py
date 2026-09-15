import base64
import io
import logging

import qrcode

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


def _vcard_escape(value):
    if not value:
        return ""
    value = value.replace("\\", "\\\\")
    # Normaliza cualquier variante de salto de línea (CRLF o CR suelto) a LF
    # antes de escaparlo: un "\r" sin escapar y sin pareja quedaría como
    # carácter de control real en la vCard, y varios lectores lo tratan como
    # separador de línea igual que "\n" — eso permitiría inyectar una
    # propiedad falsa (p.ej. otro TEL/EMAIL) en la tarjeta a través de un
    # campo de texto libre como el nombre o la dirección.
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = value.replace(";", "\\;")
    value = value.replace(",", "\\,")
    value = value.replace("\n", "\\n")
    return value


def _build_vcard_text(
    name,
    is_company,
    function=None,
    phone=None,
    email=None,
    street=None,
    street2=None,
    city=None,
    zip_code=None,
    country_name=None,
    company_name=None,
    website=None,
):
    """Construye el texto de una vCard 3.0 a partir de datos ya planos
    (sin recordset), para que sea una función pura y fácil de testear."""
    if not name:
        return ""

    escaped_name = _vcard_escape(name)
    lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{escaped_name}"]

    if is_company:
        lines.append(f"ORG:{escaped_name}")
    else:
        lines.append(f"N:;{escaped_name};;;")
        if company_name:
            lines.append(f"ORG:{_vcard_escape(company_name)}")
        if function:
            lines.append(f"TITLE:{_vcard_escape(function)}")

    if phone:
        lines.append(f"TEL;TYPE=WORK,VOICE:{_vcard_escape(phone)}")

    if email:
        lines.append(f"EMAIL;TYPE=INTERNET:{_vcard_escape(email)}")

    if street or street2 or city or zip_code or country_name:
        adr = ";{street2};{street};{city};;{zip_code};{country}".format(
            street2=_vcard_escape(street2 or ""),
            street=_vcard_escape(street or ""),
            city=_vcard_escape(city or ""),
            zip_code=_vcard_escape(zip_code or ""),
            country=_vcard_escape(country_name or ""),
        )
        lines.append(f"ADR;TYPE=WORK:{adr}")

    if website:
        lines.append(f"URL:{_vcard_escape(website)}")

    lines.append("END:VCARD")
    return "\r\n".join(lines) + "\r\n"


def _generate_qr_png(vcard_text):
    """Genera un PNG (bytes) del QR de la vCard. Nunca lanza: si algo falla
    en la generación, degrada a False para no romper la carga del
    formulario del contacto (mismo criterio que el manejo de errores del
    OCR en cositt_business_card_ocr)."""
    if not vcard_text:
        return False
    try:
        image = qrcode.make(vcard_text, error_correction=qrcode.constants.ERROR_CORRECT_M)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception:
        _logger.warning("No se pudo generar el QR de vCard", exc_info=True)
        return False


class ResPartner(models.Model):
    _inherit = "res.partner"

    # No almacenado a propósito: el QR se recalcula con los datos vigentes
    # del contacto en cada lectura. Pensado para el formulario (un registro
    # a la vez); no usar en listas/kanban/export masivo, donde generaría un
    # PNG por fila de forma síncrona en cada lectura.
    qr_vcard = fields.Binary(
        string="QR vCard",
        compute="_compute_qr_vcard",
        store=False,
        help="Código QR generado localmente con los datos de contacto en "
        "formato vCard. Escanéalo con la cámara de un móvil para "
        "añadir el contacto directamente a la agenda.",
    )

    @api.depends(
        "name",
        "is_company",
        "function",
        "phone",
        "email",
        "street",
        "street2",
        "city",
        "zip",
        "country_id.name",
        "commercial_company_name",
        "website",
    )
    def _compute_qr_vcard(self):
        for partner in self:
            try:
                vcard_text = _build_vcard_text(
                    name=partner.name,
                    is_company=partner.is_company,
                    function=partner.function,
                    phone=partner.phone,
                    email=partner.email,
                    street=partner.street,
                    street2=partner.street2,
                    city=partner.city,
                    zip_code=partner.zip,
                    country_name=partner.country_id.name,
                    company_name=partner.commercial_company_name,
                    website=partner.website,
                )
                png_bytes = _generate_qr_png(vcard_text)
            except Exception:
                # No debe romper la carga del formulario de contacto por un
                # problema puntual (p.ej. AccessError al leer country_id en
                # un escenario multi-compañía) — degrada a campo vacío.
                _logger.warning(
                    "No se pudo generar el QR vCard para el contacto %s (id=%s)",
                    partner.display_name,
                    partner.id,
                    exc_info=True,
                )
                png_bytes = False
            partner.qr_vcard = base64.b64encode(png_bytes) if png_bytes else False
