from odoo import api, models
from odoo.fields import Domain


class MailMessage(models.Model):
    _inherit = "mail.message"

    # OVERRIDE COMPLETO de mail.message._message_fetch (Odoo 19.0,
    # odoo/addons/mail/models/mail_message.py). No hay ningún hook para
    # añadir una condición al "message_domain" que construye internamente
    # (ver README: se investigó antes de tocar nada, siguiendo el resto de
    # este método al pie de la letra). Única diferencia con el original:
    # una cláusula OR más en message_domain para que el mismo cuadro de
    # búsqueda del chatter también encuentre mensajes por autor.
    # RE-DIFFEAR ESTE MÉTODO EN CADA UPGRADE DE ODOO.
    @api.model
    def _message_fetch(self, domain, *, thread=None, search_term=None, is_notification=None,
                        before=None, after=None, around=None, limit=30):
        res = {}
        domain = Domain(True if domain is None else domain)
        if thread:
            domain &= (
                Domain("res_id", "=", thread.id)
                & Domain("model", "=", thread._name)
                & Domain("message_type", "!=", "user_notification")
            )
        if is_notification is True:
            domain &= Domain("message_type", "=", "notification")
        elif is_notification is False:
            domain &= Domain("message_type", "!=", "notification")
        if search_term:
            # we replace every space by a % to avoid hard spacing matching
            search_term = search_term.replace(" ", "%")
            message_domain = Domain.OR([
                # sudo: access to attachment is allowed if you have access to the parent model
                [("attachment_ids", "in", self.env["ir.attachment"].sudo()._search([("name", "ilike", search_term)]))],
                [("body", "ilike", search_term)],
                [("subject", "ilike", search_term)],
                [("subtype_id.description", "ilike", search_term)],
                # --- cositt_chatter_search: único añadido sobre el core ---
                # sudo: mismo criterio que la línea de adjuntos de arriba
                # (documentado por el propio core): el acceso real lo sigue
                # decidiendo el search() de mail.message de más abajo (sin
                # sudo), que solo devuelve mensajes de hilos a los que el
                # usuario ya tiene acceso. Necesario porque un usuario sin
                # el grupo interno (p. ej. base.public_user) no tiene ACL
                # de lectura sobre res.partner/mail.guest en todos los
                # casos, y el traversal "campo.subcampo" del ORM exige esa
                # ACL aunque el resultado final se vaya a filtrar igual.
                [("author_id", "in", self.env["res.partner"].sudo()._search([("name", "ilike", search_term)]))],
                [("email_from", "ilike", search_term)],
                [("author_guest_id", "in", self.env["mail.guest"].sudo()._search([("name", "ilike", search_term)]))],
                # --- fin del añadido ---
            ])
            if thread and is_notification is not False:
                tracking_value_domain = (
                    Domain("mail_message_id.res_id", "=", thread.id)
                    & Domain("mail_message_id.model", "=", thread._name)
                    & self._get_tracking_values_domain(search_term)
                )
                # sudo: mail.tracking.value - searching allowed tracking values for acessible records
                tracking_values = self.env["mail.tracking.value"].sudo().search(tracking_value_domain)
                accessible_tracking_value_ids = tracking_values._filter_has_field_access(self.env)
                message_domain |= Domain("id", "in", accessible_tracking_value_ids.mail_message_id.ids)
            domain &= message_domain
        if search_term or is_notification is not None:
            res["count"] = self.search_count(domain)
        if around is not None:
            messages_before = self.search(domain & Domain("id", "<=", around), limit=limit // 2, order="id DESC")
            messages_after = self.search(domain & Domain("id", ">", around), limit=limit // 2, order="id ASC")
            return {**res, "messages": (messages_after + messages_before).sorted("id", reverse=True)}
        if before:
            domain &= Domain("id", "<", before)
        if after:
            domain &= Domain("id", ">", after)
        res["messages"] = self.search(domain, limit=limit, order="id ASC" if after else "id DESC")
        if after:
            res["messages"] = res["messages"].sorted("id", reverse=True)
        return res
