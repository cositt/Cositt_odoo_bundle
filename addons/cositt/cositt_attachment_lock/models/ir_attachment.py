import logging

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

CONFIG_PARAM = "cositt_attachment_lock.enabled"
OVERRIDE_GROUP_XMLID = "cositt_attachment_lock.group_cositt_attachment_lock_override"


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.ondelete(at_uninstall=False)
    def _unlink_except_locked_attachment(self):
        # Se investigó el ciclo de vida interno de adjuntos de Odoo antes
        # de escribir esto (paquetes de assets, adjuntos técnicos, GC...)
        # — ver README para el detalle y las referencias al código fuente
        # de Odoo. Nunca bloquea:
        if self.env.su:
            # Todo lo que Odoo borra internamente (paquetes de assets en
            # base/models/assetsbundle.py, limpiezas @api.autovacuum...)
            # ya se ejecuta con sudo()/SUPERUSER_ID — verificado leyendo
            # ese código, no asumido. Un usuario normal por RPC nunca
            # tiene env.su=True, así que esto no abre ningún atajo real.
            return

        # sudo: leer un parámetro de configuración global — el mismo
        # patrón que usa internamente cualquier campo de
        # res.config.settings con config_parameter=. No decide nada
        # sensible por sí solo, solo si la protección está activada.
        enabled = self.env["ir.config_parameter"].sudo().get_param(CONFIG_PARAM)
        if (enabled or "").lower() != "true":
            return

        if self.env.user.has_group(OVERRIDE_GROUP_XMLID):
            return

        protected = self.filtered(
            lambda attachment: attachment.res_model and not attachment.res_field
        )
        if not protected:
            # Sin registro vinculado (borradores/adjuntos temporales) o
            # es el valor almacenado de un campo binario concreto
            # (auto-generado/gestionado por el propio ORM, no algo que
            # un humano haya adjuntado a mano): fuera del alcance de la
            # protección.
            return

        _logger.warning(
            "Blocked deletion attempt of %d protected attachment(s) by "
            "user %s (uid=%s): %s",
            len(protected), self.env.user.login, self.env.uid,
            protected.mapped("name"),
        )
        raise UserError(_(
            "No puedes eliminar adjuntos mientras la protección esté "
            "activada. Pide a un administrador que la desactive en "
            "Ajustes, o que te añada al grupo que puede eliminarlos "
            "igualmente."
        ))
