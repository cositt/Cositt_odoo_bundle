import base64

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.mimetypes import guess_mimetype

# Solo PNG a propósito: formato recomendado para favicons modernos
# (transparencia real, sin la ambigüedad de compresión con pérdida de
# JPEG para un icono tan pequeño) y el único que todos los navegadores
# soportan sin más lío que un <link rel="shortcut icon">. .ico no se
# admite: Pillow (usado por fields.Image para redimensionar) no lo
# decodifica de forma fiable en este build de Odoo — mismo tipo de
# hallazgo que el WEBP de cositt_login_background.
ALLOWED_FAVICON_MIMETYPES = {"image/png"}

# Un favicon nunca necesita más resolución que esto — cualquier
# navegador lo re-escala él mismo.
FAVICON_MAX_SIZE = 256

MAX_FAVICON_BYTES = 512 * 1024  # 512 KB

MAX_BROWSER_TITLE_LENGTH = 60


class ResCompany(models.Model):
    _inherit = "res.company"

    cositt_branding_enabled = fields.Boolean(
        string="Marca de navegador activa",
        default=False,
        help="Interruptor único para favicon y título de pestaña "
        "personalizados. Mientras esté desactivado, el sitio se ve "
        "exactamente igual que sin este módulo instalado.",
    )
    cositt_favicon_image = fields.Image(
        string="Favicon",
        max_width=FAVICON_MAX_SIZE,
        max_height=FAVICON_MAX_SIZE,
        help="Solo PNG. Se usa como icono de la pestaña del navegador "
        "en todo el sitio (backend, login y portal).",
    )
    cositt_browser_title = fields.Char(
        string="Título de pestaña del navegador",
        help="Reemplaza el título por defecto (\"Odoo\") en /web/login "
        "y páginas sin JS. En el backend, se añade como parte del "
        "título junto al nombre de la vista actual.",
    )

    @api.constrains("cositt_favicon_image")
    def _check_cositt_favicon_image(self):
        for company in self:
            if not company.cositt_favicon_image:
                continue
            raw = base64.b64decode(company.cositt_favicon_image)
            size = len(raw)
            if size > MAX_FAVICON_BYTES:
                raise ValidationError(_(
                    "El favicon no puede superar %(limit)s KB "
                    "(actual: %(size).0f KB)."
                ) % {
                    "limit": MAX_FAVICON_BYTES // 1024,
                    "size": size / 1024,
                })
            mimetype = guess_mimetype(raw)
            if mimetype not in ALLOWED_FAVICON_MIMETYPES:
                raise ValidationError(_(
                    'Formato de imagen no admitido ("%(mimetype)s"). '
                    "Usa PNG."
                ) % {"mimetype": mimetype})

    @api.constrains("cositt_browser_title")
    def _check_cositt_browser_title_length(self):
        for company in self:
            title = company.cositt_browser_title
            if title and len(title) > MAX_BROWSER_TITLE_LENGTH:
                raise ValidationError(_(
                    "El título de pestaña no puede superar "
                    "%(limit)s caracteres (actual: %(length)s)."
                ) % {
                    "limit": MAX_BROWSER_TITLE_LENGTH,
                    "length": len(title),
                })

    def _cositt_get_favicon_url(self):
        """URL lista para inyectar en x_icon (ver
        views/webclient_templates.xml), o False si no hay nada que
        aplicar."""
        self.ensure_one()
        if not self.cositt_branding_enabled or not self.cositt_favicon_image:
            return False
        return "/web/image/res.company/%s/cositt_favicon_image" % self.id

    def _cositt_get_browser_title(self):
        """String listo para inyectar en title (ver
        views/webclient_templates.xml) y en session_info() (ver
        ir_http.py), o False si no hay nada que aplicar."""
        self.ensure_one()
        if not self.cositt_branding_enabled:
            return False
        return self.cositt_browser_title or False
