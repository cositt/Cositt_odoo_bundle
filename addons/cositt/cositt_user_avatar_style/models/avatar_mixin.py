import base64
from hashlib import sha512

from odoo import api, models
from odoo.exceptions import AccessError
from odoo.tools import html_escape


class AvatarMixin(models.AbstractModel):
    _inherit = "avatar.mixin"

    # _avatar_generate_svg() (abajo) lee self.env.company, pero Odoo solo
    # sabe que un campo computado depende de la compañía activa si el
    # método asignado a compute= lo declara explícitamente — si no, cachea
    # el valor por registro sin distinguir compañía, y una misma sesión
    # que cambie de compañía a mitad de transacción (with_company) vería
    # el color de la compañía equivocada. Redeclarar el compute con
    # @api.depends_context("company") arregla eso; @api.depends(...) del
    # core (mismo nombre de método) se sigue aplicando igual, Odoo fusiona
    # las dependencias de todas las clases que definen el mismo compute.
    @api.depends_context("company")
    def _compute_avatar_1920(self):
        return super()._compute_avatar_1920()

    @api.depends_context("company")
    def _compute_avatar_1024(self):
        return super()._compute_avatar_1024()

    @api.depends_context("company")
    def _compute_avatar_512(self):
        return super()._compute_avatar_512()

    @api.depends_context("company")
    def _compute_avatar_256(self):
        return super()._compute_avatar_256()

    @api.depends_context("company")
    def _compute_avatar_128(self):
        return super()._compute_avatar_128()

    def _avatar_generate_svg(self):
        # Estructura del SVG idéntica a la del core
        # (odoo/addons/base/models/avatar_mixin.py::_avatar_generate_svg)
        # — solo cambia CÓMO se elige el color de fondo. Se hereda de
        # avatar.mixin (no de res.partner ni de un modelo concreto) a
        # propósito: aplica por igual a cualquier modelo que use este
        # mixin (res.partner, hr.employee, etc.), no solo a Contactos.
        # Re-diffear contra el core en cada upgrade de Odoo.
        #
        # env.company puede lanzar AccessError si el contexto trae
        # allowed_company_ids con una compañía fuera de las permitidas
        # al usuario actual y el env no está en sudo (mismo tipo de bug
        # ya encontrado como HIGH en cositt_contact_qr_vcard de este
        # proyecto) — un avatar nunca debería tumbar la lectura de todo
        # un lote de registros por esto, cae al color nativo de Odoo.
        try:
            palette = self.env.company._cositt_get_avatar_palette()
        except AccessError:
            return super()._avatar_generate_svg()
        if not palette:
            return super()._avatar_generate_svg()
        initial = html_escape(self[self._avatar_name_field][0].upper())
        seed = self[self._avatar_name_field] + str(
            self.create_date.timestamp() if self.create_date else ""
        )
        index = int(sha512(seed.encode()).hexdigest(), 16) % len(palette)
        bgcolor = palette[index]
        return base64.b64encode((
            "<?xml version='1.0' encoding='UTF-8' ?>"
            "<svg height='180' width='180' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>"
            f"<rect fill='{bgcolor}' height='180' width='180'/>"
            f"<text fill='#ffffff' font-size='96' text-anchor='middle' x='90' y='125' font-family='sans-serif'>{initial}</text>"
            "</svg>"
        ).encode())
