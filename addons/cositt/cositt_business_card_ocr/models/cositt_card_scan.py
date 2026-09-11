import base64

from odoo import _, fields, models
from odoo.exceptions import UserError

from . import ocr_provider
from .card_parser import normalize_phone_digits, parse_card_text


class CosittCardScan(models.Model):
    _name = "cositt.card.scan"
    _description = "Escaneo de tarjeta de visita"
    _order = "id desc"

    name = fields.Char(default="Nuevo escaneo", required=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    image = fields.Binary(string="Foto de la tarjeta", attachment=True)
    image_filename = fields.Char()
    raw_text = fields.Text(string="Texto detectado", readonly=True)

    partner_name = fields.Char(string="Nombre")
    function = fields.Char(string="Cargo")
    company_name = fields.Char(string="Empresa")
    email = fields.Char()
    phone = fields.Char()
    mobile = fields.Char()
    website = fields.Char()
    street = fields.Char(string="Dirección")

    duplicate_partner_id = fields.Many2one(
        "res.partner", string="Posible duplicado", readonly=True
    )
    parent_partner_id = fields.Many2one(
        "res.partner",
        string="Añadir como contacto de",
        domain=[("is_company", "=", True)],
        help="Si se indica, el contacto se crea como persona de esta empresa.",
    )
    partner_id = fields.Many2one("res.partner", string="Contacto creado", readonly=True)

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("scanned", "Escaneado"),
            ("done", "Confirmado"),
            ("discarded", "Descartado"),
        ],
        default="draft",
        required=True,
    )

    def action_scan(self):
        self.ensure_one()
        if not self.image:
            raise UserError(_("Sube primero una foto de la tarjeta."))

        image_bytes = base64.b64decode(self.image)
        try:
            raw_text = ocr_provider.extract_text(image_bytes)
        except Exception as exc:
            raise UserError(
                _(
                    "No se pudo procesar la imagen. Comprueba que es una foto "
                    "válida y que el servidor tiene Tesseract OCR disponible."
                )
            ) from exc
        parsed = parse_card_text(raw_text)

        self._find_duplicate(parsed)
        self.write(
            {
                "raw_text": raw_text,
                "state": "scanned",
                **parsed,
            }
        )

    def _find_duplicate(self, parsed):
        # Odoo 19 unificó "mobile" dentro de "phone" en res.partner (ya no
        # existe un campo mobile separado), por eso ambos valores se buscan
        # sobre el mismo campo.
        Partner = self.env["res.partner"]
        partner = Partner.browse()

        email = (parsed.get("email") or "").strip()
        if email:
            partner = Partner.search([("email", "=ilike", email)], limit=1)

        for phone_value in (parsed.get("phone"), parsed.get("mobile")):
            if partner or not phone_value:
                continue
            digits = normalize_phone_digits(phone_value)
            if not digits:
                continue
            partner = Partner.search(
                [("phone_sanitized", "like", digits)], limit=1
            ) or Partner.search([("phone", "like", digits)], limit=1)

        self.duplicate_partner_id = partner.id if partner else False

    def action_link_existing(self):
        self.ensure_one()
        if self.state != "scanned":
            raise UserError(_("Este escaneo ya no está en estado 'Escaneado'."))
        if not self.duplicate_partner_id:
            raise UserError(_("No hay ningún contacto detectado para vincular."))
        self.write({"partner_id": self.duplicate_partner_id.id, "state": "done"})

    def action_confirm(self):
        self.ensure_one()
        if self.state != "scanned":
            raise UserError(_("Este escaneo ya no está en estado 'Escaneado'."))

        vals = {
            "name": self.partner_name or self.company_name or _("Contacto sin nombre"),
            "function": self.function,
            "email": self.email,
            "phone": self.mobile or self.phone,
            "website": self.website,
            "street": self.street,
            "company_id": self.company_id.id,
        }
        if self.parent_partner_id:
            vals["parent_id"] = self.parent_partner_id.id
        elif self.company_name and not self.partner_name:
            vals["is_company"] = True
        elif self.company_name:
            vals["company_name"] = self.company_name

        partner = self.env["res.partner"].create(vals)
        self.write({"partner_id": partner.id, "state": "done"})
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "form",
            "res_id": partner.id,
        }

    def action_discard(self):
        self.write({"state": "discarded"})
