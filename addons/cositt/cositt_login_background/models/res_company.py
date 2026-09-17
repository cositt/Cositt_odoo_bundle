import base64
import re

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.mimetypes import guess_mimetype

# Mismo hallazgo que en cositt_home_wallpaper (módulo independiente,
# constantes propias a propósito — ver README del bundle sobre
# independencia entre módulos Cositt): fields.Image no rechaza SVG por
# sí solo, ImageProcess lo deja pasar sin procesar. Se valida el
# mimetype real del contenido decodificado.
ALLOWED_LOGIN_BG_MIMETYPES = {"image/jpeg", "image/png", "image/webp"}

# Límite propio, más estricto que el límite global de subida de Odoo
# (`web.max_file_upload_size`, 128 MB por defecto). Verificado tras el
# resize automático de fields.Image más abajo.
MAX_LOGIN_BG_BYTES = 5 * 1024 * 1024  # 5 MB

# La pantalla de login nunca ocupa más que el viewport de una pantalla
# de escritorio real; 2560x1440 cubre con margen cualquier resolución
# habitual sin guardar archivos innecesariamente pesados.
#
# Hallazgo real verificado (no supuesto): este redimensionado NO se
# aplica a WEBP. odoo/tools/image.py endurece Pillow a propósito
# (`Image.preinit()` + `Image._initialized = 2`, un subconjunto mínimo
# de formatos, sin auto-registro completo bajo demanda) — dentro del
# proceso de Odoo, Pillow no puede decodificar/codificar WEBP, así que
# `image_process()` detecta el WEBP por sus bytes mágicos
# (RIFF/WEBPVP8) y lo guarda TAL CUAL, sin pasar por el resize (mismo
# trato que ya recibe SVG). MAX_LOGIN_BG_BYTES sigue aplicando sobre el
# archivo tal cual se sube, así que el límite de tamaño real no se
# pierde — solo el redimensionado automático no alcanza a este formato.
LOGIN_BG_MAX_WIDTH = 2560
LOGIN_BG_MAX_HEIGHT = 1440

# Blur en CSS por encima de ~40px no aporta diferencia visual
# perceptible y sí un coste de repintado mayor.
MAX_LOGIN_BG_BLUR = 40

COLOR_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

FIT_TO_CSS_SIZE = {
    "cover": "cover",
    "contain": "contain",
    "center": "auto",
    "stretch": "100% 100%",
}

POSITION_TO_CSS_POSITION = {
    "center": "center center",
    "top": "center top",
    "bottom": "center bottom",
}


class ResCompany(models.Model):
    _inherit = "res.company"

    cositt_login_bg_enabled = fields.Boolean(
        string="Fondo de login activo",
        default=False,
        help="Mientras esté desactivado, la pantalla de login se ve "
        "exactamente igual que sin este módulo instalado.",
    )
    cositt_login_bg_image = fields.Image(
        string="Imagen de fondo de login",
        max_width=LOGIN_BG_MAX_WIDTH,
        max_height=LOGIN_BG_MAX_HEIGHT,
        help="Formatos admitidos: JPG, PNG, WEBP. SVG no se admite.",
    )
    cositt_login_bg_color = fields.Char(
        string="Color de fondo de login",
        help="Color de respaldo/base en formato hexadecimal (#rrggbb). "
        "Se ve mientras la imagen carga o si no se sube ninguna.",
    )
    cositt_login_bg_overlay = fields.Integer(
        string="Oscurecimiento de login (%)",
        default=25,
        help="0 = sin capa oscura sobre la imagen. 100 = completamente "
        "oscurecida. Ayuda a mantener legible el formulario de login "
        "sobre imágenes claras o con mucho detalle.",
    )
    cositt_login_bg_blur = fields.Integer(
        string="Desenfoque de login (px)",
        default=0,
        help="Desenfoque aplicado solo a la imagen de fondo, nunca al "
        "formulario de login.",
    )
    cositt_login_bg_fit = fields.Selection(
        [
            ("cover", "Cubrir (recorta para llenar la pantalla)"),
            ("contain", "Contener (se ve completa, puede dejar bordes)"),
            ("center", "Centrada sin ajustar"),
            ("stretch", "Estirar (llena la pantalla sin recortar)"),
        ],
        string="Ajuste de imagen de login",
        default="cover",
    )
    cositt_login_bg_position = fields.Selection(
        [
            ("center", "Centro"),
            ("top", "Arriba"),
            ("bottom", "Abajo"),
        ],
        string="Posición de login",
        default="center",
    )

    @api.constrains("cositt_login_bg_image")
    def _check_cositt_login_bg_image(self):
        for company in self:
            if not company.cositt_login_bg_image:
                continue
            raw = base64.b64decode(company.cositt_login_bg_image)
            size = len(raw)
            if size > MAX_LOGIN_BG_BYTES:
                raise ValidationError(_(
                    "La imagen de fondo no puede superar %(limit)s MB "
                    "(actual: %(size).1f MB)."
                ) % {
                    "limit": MAX_LOGIN_BG_BYTES // (1024 * 1024),
                    "size": size / (1024 * 1024),
                })
            mimetype = guess_mimetype(raw)
            if mimetype not in ALLOWED_LOGIN_BG_MIMETYPES:
                raise ValidationError(_(
                    'Formato de imagen no admitido ("%(mimetype)s"). '
                    "Usa JPG, PNG o WEBP."
                ) % {"mimetype": mimetype})

    @api.constrains("cositt_login_bg_color")
    def _check_cositt_login_bg_color(self):
        for company in self:
            color = company.cositt_login_bg_color
            if color and not COLOR_HEX_RE.match(color):
                raise ValidationError(_(
                    'Color de fondo no válido: "%s". Usa el formato '
                    "hexadecimal #rrggbb (ej. #1a2b3c)."
                ) % color)

    @api.constrains("cositt_login_bg_overlay")
    def _check_cositt_login_bg_overlay(self):
        for company in self:
            if not 0 <= company.cositt_login_bg_overlay <= 100:
                raise ValidationError(
                    _("El oscurecimiento debe estar entre 0 y 100.")
                )

    @api.constrains("cositt_login_bg_blur")
    def _check_cositt_login_bg_blur(self):
        for company in self:
            if not 0 <= company.cositt_login_bg_blur <= MAX_LOGIN_BG_BLUR:
                raise ValidationError(_(
                    "El desenfoque debe estar entre 0 y %(max)s px."
                ) % {"max": MAX_LOGIN_BG_BLUR})

    def action_cositt_reset_login_bg(self):
        self.write({
            "cositt_login_bg_enabled": False,
            "cositt_login_bg_image": False,
            "cositt_login_bg_color": False,
            "cositt_login_bg_overlay": 25,
            "cositt_login_bg_blur": 0,
            "cositt_login_bg_fit": "cover",
            "cositt_login_bg_position": "center",
        })
        return True

    def _cositt_get_login_bg_config(self):
        """Config lista para inyectar como propiedades CSS en el <head>
        de la pantalla de login (ver views/webclient_templates.xml).
        Todos los valores ya vienen mapeados a CSS válido aquí — la
        plantilla QWeb solo interpola, no decide nada.

        LIMITACIÓN CONOCIDA (multiempresa, encontrada en code review,
        no en desarrollo inicial): la plantilla llama a este método
        sobre `request.env.company`. Para un visitante anónimo de
        /web/login, Odoo resuelve `env.company` a
        `base.public_user.company_id` (fijado en el alta de la base,
        nunca cambia solo) — NO a una compañía elegida en el momento
        del login, porque en ese punto el visitante aún no se ha
        autenticado como nadie. Con una sola compañía (el caso de este
        entorno de desarrollo) esto es invisible; en una instalación
        real multiempresa, todas las visitas anónimas verían siempre
        el fondo de la MISMA compañía (la de public_user), nunca el de
        otra, aunque cada una tenga su propia configuración guardada
        aquí. Resolverlo de verdad exigiría un mecanismo de detección
        de compañía por dominio/subdominio (terreno de `website`, fuera
        de alcance a propósito — ver README). Documentado como
        limitación conocida del MVP, no como bug oculto.
        """
        self.ensure_one()
        if not self.cositt_login_bg_enabled:
            return {"enabled": False}
        image_url = (
            "/web/image/res.company/%s/cositt_login_bg_image" % self.id
            if self.cositt_login_bg_image else False
        )
        # Markup(), no texto plano: estos valores se interpolan dentro
        # de un <style> en la plantilla (t-out). Un <style> es "raw
        # text" en HTML — el navegador NO decodifica entidades ahí — así
        # que el escapado normal de t-out (comillas -> &#34;) rompía el
        # url(...) en vez de protegerlo (bug real, encontrado en
        # verificación manual: la imagen no cargaba, la URL quedaba con
        # "&#34;" literal dentro del CSS). Es seguro marcarlos como
        # Markup porque cada uno ya viene de una fuente controlada, no
        # de texto libre: css_image se construye aquí mismo a partir de
        # self.id (entero), color ya pasó _check_cositt_login_bg_color
        # (regex estricto #rrggbb), y css_size/css_position solo pueden
        # ser uno de los pocos valores fijos de los diccionarios de
        # abajo.
        return {
            "enabled": True,
            "css_image": Markup('url("%s")' % image_url) if image_url else Markup("none"),
            "color": Markup(self.cositt_login_bg_color) if self.cositt_login_bg_color else Markup("transparent"),
            "css_size": Markup(FIT_TO_CSS_SIZE.get(self.cositt_login_bg_fit, "cover")),
            "css_position": Markup(POSITION_TO_CSS_POSITION.get(
                self.cositt_login_bg_position, "center center"
            )),
            "blur": self.cositt_login_bg_blur,
            "overlay_ratio": (self.cositt_login_bg_overlay or 0) / 100,
        }
