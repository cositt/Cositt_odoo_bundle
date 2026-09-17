from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

MAX_WATERMARK_ROTATION = 180


class ResCompany(models.Model):
    _inherit = "res.company"

    cositt_watermark_enabled = fields.Boolean(
        string="Marca de agua activa",
        default=False,
        help="Mientras esté desactivado, los reportes PDF se ven "
        "exactamente igual que sin este módulo instalado.",
    )
    cositt_watermark_text = fields.Char(
        string="Texto de marca de agua",
        help='Ej. "BORRADOR", "COPIA", "CONFIDENCIAL". Se muestra en '
        "TODOS los reportes PDF del sistema.",
    )
    cositt_watermark_opacity = fields.Integer(
        string="Opacidad (%)",
        default=12,
        help="0 = invisible. 100 = completamente opaco. Un valor bajo "
        "(10-20%) es lo habitual para no dificultar la lectura del "
        "documento debajo.",
    )
    cositt_watermark_rotation = fields.Integer(
        string="Rotación (grados)",
        default=-45,
        help="Ángulo de rotación del texto, en grados (-180 a 180). "
        "-45 es la diagonal clásica de una marca de agua.",
    )

    @api.constrains("cositt_watermark_enabled", "cositt_watermark_text")
    def _check_watermark_text_required_when_enabled(self):
        for company in self:
            if company.cositt_watermark_enabled and not company.cositt_watermark_text:
                raise ValidationError(_(
                    "Activaste la marca de agua pero no pusiste ningún "
                    "texto — no habría nada que mostrar."
                ))

    @api.constrains("cositt_watermark_opacity")
    def _check_watermark_opacity(self):
        for company in self:
            if not 0 <= company.cositt_watermark_opacity <= 100:
                raise ValidationError(_("La opacidad debe estar entre 0 y 100."))

    @api.constrains("cositt_watermark_rotation")
    def _check_watermark_rotation(self):
        for company in self:
            if not -MAX_WATERMARK_ROTATION <= company.cositt_watermark_rotation <= MAX_WATERMARK_ROTATION:
                raise ValidationError(_(
                    "La rotación debe estar entre -%(max)s y %(max)s grados."
                ) % {"max": MAX_WATERMARK_ROTATION})

    def action_cositt_reset_watermark(self):
        self.write({
            "cositt_watermark_enabled": False,
            "cositt_watermark_text": False,
            "cositt_watermark_opacity": 12,
            "cositt_watermark_rotation": -45,
        })
        return True

    def _cositt_get_watermark_config(self):
        """Config lista para interpolar en el <div> de la marca de
        agua (ver views/report_templates.xml). Se llama con `env.company`
        directamente desde la plantilla de reporte — sin sesión HTTP,
        sin session_info(): `env` ya está disponible en cualquier
        render QWeb de reporte (igual que en decenas de plantillas del
        propio core, ej. `t-set="company" t-value="env.company"` en
        web/views/report_templates.xml).

        LIMITACIÓN CONOCIDA (multiempresa, mismo espíritu que la de
        cositt_login_background): usa la compañía activa del entorno
        de renderizado, no necesariamente la compañía del registro
        concreto que se imprime. En instalaciones de una sola compañía
        (el caso de este entorno) es invisible; en multiempresa real,
        conviene verificar que la acción de impresión resuelve la
        compañía esperada antes de depender de esto para documentos
        legales sensibles.
        """
        self.ensure_one()
        if not self.cositt_watermark_enabled:
            return {"enabled": False}
        return {
            "enabled": True,
            "text": self.cositt_watermark_text,
            "opacity_ratio": self.cositt_watermark_opacity / 100,
            "rotation": self.cositt_watermark_rotation,
        }
