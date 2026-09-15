from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import email_domain_extract

# Proveedores de email genéricos/personales: que dos contactos compartan
# "gmail.com" no significa que trabajen en la misma empresa, así que se
# excluyen de la búsqueda de empresa por dominio. Lista no exhaustiva
# (mercado español) — ampliable si aparecen más casos reales.
FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "hotmail.com",
    "hotmail.es",
    "outlook.com",
    "outlook.es",
    "live.com",
    "live.es",
    "icloud.com",
    "me.com",
    "yahoo.com",
    "yahoo.es",
    "aol.com",
    "protonmail.com",
    "proton.me",
    "gmx.com",
    "gmx.es",
    "mail.com",
    "yandex.com",
}


class ResPartner(models.Model):
    _inherit = "res.partner"

    email_domain = fields.Char(
        string="Email domain",
        compute="_compute_email_domain",
        store=True,
        index=True,
    )

    @api.depends("email")
    def _compute_email_domain(self):
        for partner in self:
            partner.email_domain = (
                email_domain_extract(partner.email) if partner.email else False
            )

    def action_find_company_by_domain(self):
        self.ensure_one()
        if self.is_company:
            raise UserError(
                _("Esto solo aplica a personas de contacto, no a empresas.")
            )
        if not self.email_domain:
            raise UserError(
                _(
                    "No se pudo determinar un dominio de email único para "
                    "este contacto."
                )
            )
        if self.email_domain in FREE_EMAIL_DOMAINS:
            raise UserError(
                _(
                    'El dominio "%s" es de un proveedor de email genérico '
                    "(Gmail, Outlook...) y no identifica una empresa."
                )
                % self.email_domain
            )

        companies = self.env["res.partner"].search(
            [("is_company", "=", True), ("email_domain", "=", self.email_domain)],
            limit=2,
        )
        if not companies:
            raise UserError(
                _('No se encontró ninguna empresa con el dominio "%s".')
                % self.email_domain
            )
        if self.parent_id and self.parent_id in companies:
            raise UserError(
                _('Este contacto ya está vinculado a "%s".')
                % self.parent_id.display_name
            )
        # Contacto ya vinculado a OTRA empresa (p.ej. asignada a mano, o sin
        # relación con este dominio): no reasignar en silencio y perder ese
        # vínculo sin que el usuario se entere, exigir que lo desvincule antes.
        if self.parent_id:
            raise UserError(
                _(
                    'Este contacto ya está vinculado a "%(current)s". '
                    'Desvincúlalo primero si quieres asociarlo a "%(found)s".'
                )
                % {
                    "current": self.parent_id.display_name,
                    "found": companies[0].display_name,
                }
            )
        if len(companies) > 1:
            raise UserError(
                _(
                    'Hay varias empresas distintas con el dominio "%s". '
                    "Revísalo manualmente."
                )
                % self.email_domain
            )

        self.parent_id = companies.id
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Empresa asociada"),
                "message": _('Contacto vinculado a "%s".') % companies.display_name,
                "type": "success",
            },
        }
