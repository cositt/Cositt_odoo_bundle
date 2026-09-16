import base64
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.mimetypes import guess_mimetype

# fields.Image (vía ImageProcess, odoo/tools/image.py) deja pasar SVG
# SIN procesar a propósito ("don't process... if the image is SVG",
# comprobado leyendo el código fuente: cualquier contenido que empiece
# por b'<' se guarda tal cual) — no lo rechaza por sí solo. Se valida
# aquí explícitamente el mimetype real del contenido decodificado
# porque un SVG puede contener JavaScript embebido y Odoo no lo
# sanea en este campo.
ALLOWED_WALLPAPER_MIMETYPES = {"image/jpeg", "image/png", "image/webp"}

# Tras el resize automático de fields.Image (max_width/max_height más
# abajo), el archivo final guardado no debería acercarse ni de lejos a
# este límite en la inmensa mayoría de los casos; se mantiene como
# límite explícito y documentado (no silencioso) por si un formato con
# compresión pobre (ej. un PNG con mucho detalle) se resiste al resize.
# Odoo ya impone un límite global de subida (`web.max_file_upload_size`,
# 128 MB por defecto) para cualquier binario — este límite es una regla
# de negocio propia de este módulo, más estricta, no una sustitución.
MAX_WALLPAPER_BYTES = 5 * 1024 * 1024  # 5 MB

# Una imagen de fondo de Home Menu no necesita más resolución que la
# pantalla más grande razonable (4K a ancho completo ronda 3840px, pero
# el propio Home Menu nunca ocupa el 100% del ancho ni ese nivel de
# detalle aporta nada perceptible en un fondo). 2560x1440 cubre con
# margen cualquier resolución de escritorio real sin guardar archivos
# innecesariamente pesados.
WALLPAPER_MAX_WIDTH = 2560
WALLPAPER_MAX_HEIGHT = 1440

# Blur en CSS por encima de ~40px no aporta diferencia visual perceptible
# sobre una imagen de fondo y sí un coste de repintado mayor — rango
# acotado a propósito, no arbitrario.
MAX_WALLPAPER_BLUR = 40

COLOR_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class ResCompany(models.Model):
    _inherit = "res.company"

    cositt_wallpaper_enabled = fields.Boolean(
        string="Fondo personalizado activo",
        default=False,
        help="Mientras esté desactivado, el Home Menu se ve exactamente "
        "igual que sin este módulo instalado.",
    )
    cositt_wallpaper_image = fields.Image(
        string="Imagen de fondo",
        max_width=WALLPAPER_MAX_WIDTH,
        max_height=WALLPAPER_MAX_HEIGHT,
        help="Formatos admitidos: JPG, PNG, WEBP. SVG no se admite "
        "(Pillow, usado internamente por Odoo para procesar la imagen, "
        "no lo decodifica).",
    )
    cositt_wallpaper_color = fields.Char(
        string="Color de fondo",
        help="Color de respaldo/base en formato hexadecimal (#rrggbb). "
        "Se ve mientras la imagen carga o si no se sube ninguna.",
    )
    cositt_wallpaper_overlay = fields.Integer(
        string="Oscurecimiento (%)",
        default=25,
        help="0 = sin capa oscura sobre la imagen. 100 = completamente "
        "oscurecida. Ayuda a mantener legibles los iconos y el texto "
        "sobre imágenes claras o con mucho detalle.",
    )
    cositt_wallpaper_blur = fields.Integer(
        string="Desenfoque (px)",
        default=0,
        help="Desenfoque aplicado solo a la imagen de fondo, nunca a los "
        "iconos ni al texto del Home Menu.",
    )
    cositt_wallpaper_fit = fields.Selection(
        [
            ("cover", "Cubrir (recorta para llenar la pantalla)"),
            ("contain", "Contener (se ve completa, puede dejar bordes)"),
            ("center", "Centrada sin ajustar"),
            ("stretch", "Estirar (llena la pantalla sin recortar)"),
        ],
        string="Ajuste de imagen",
        default="cover",
    )
    cositt_wallpaper_position = fields.Selection(
        [
            ("center", "Centro"),
            ("top", "Arriba"),
            ("bottom", "Abajo"),
        ],
        string="Posición",
        default="center",
    )

    @api.constrains("cositt_wallpaper_image")
    def _check_cositt_wallpaper_image(self):
        for company in self:
            if not company.cositt_wallpaper_image:
                continue
            raw = base64.b64decode(company.cositt_wallpaper_image)
            size = len(raw)
            if size > MAX_WALLPAPER_BYTES:
                raise ValidationError(_(
                    "La imagen de fondo no puede superar %(limit)s MB "
                    "(actual: %(size).1f MB)."
                ) % {
                    "limit": MAX_WALLPAPER_BYTES // (1024 * 1024),
                    "size": size / (1024 * 1024),
                })
            mimetype = guess_mimetype(raw)
            if mimetype not in ALLOWED_WALLPAPER_MIMETYPES:
                raise ValidationError(_(
                    'Formato de imagen no admitido ("%(mimetype)s"). '
                    "Usa JPG, PNG o WEBP."
                ) % {"mimetype": mimetype})

    @api.constrains("cositt_wallpaper_color")
    def _check_cositt_wallpaper_color(self):
        for company in self:
            color = company.cositt_wallpaper_color
            if color and not COLOR_HEX_RE.match(color):
                raise ValidationError(_(
                    'Color de fondo no válido: "%s". Usa el formato '
                    "hexadecimal #rrggbb (ej. #1a2b3c)."
                ) % color)

    @api.constrains("cositt_wallpaper_overlay")
    def _check_cositt_wallpaper_overlay(self):
        for company in self:
            if not 0 <= company.cositt_wallpaper_overlay <= 100:
                raise ValidationError(
                    _("El oscurecimiento debe estar entre 0 y 100.")
                )

    @api.constrains("cositt_wallpaper_blur")
    def _check_cositt_wallpaper_blur(self):
        for company in self:
            if not 0 <= company.cositt_wallpaper_blur <= MAX_WALLPAPER_BLUR:
                raise ValidationError(_(
                    "El desenfoque debe estar entre 0 y %(max)s px."
                ) % {"max": MAX_WALLPAPER_BLUR})

    def action_cositt_reset_wallpaper(self):
        self.write({
            "cositt_wallpaper_enabled": False,
            "cositt_wallpaper_image": False,
            "cositt_wallpaper_color": False,
            "cositt_wallpaper_overlay": 25,
            "cositt_wallpaper_blur": 0,
            "cositt_wallpaper_fit": "cover",
            "cositt_wallpaper_position": "center",
        })
        return True

    def _cositt_get_wallpaper_config(self):
        """Config lista para exponer en session_info: nunca incluye el
        binario, solo la URL servida por el controlador estándar de
        Odoo (/web/image/..., con su propia caché por ETag/write_date
        ya resuelta por el core, no hace falta reinventarla aquí)."""
        self.ensure_one()
        if not self.cositt_wallpaper_enabled:
            return {"enabled": False}
        return {
            "enabled": True,
            "image_url": (
                "/web/image/res.company/%s/cositt_wallpaper_image" % self.id
                if self.cositt_wallpaper_image else False
            ),
            "color": self.cositt_wallpaper_color or False,
            "overlay": self.cositt_wallpaper_overlay,
            "blur": self.cositt_wallpaper_blur,
            "fit": self.cositt_wallpaper_fit,
            "position": self.cositt_wallpaper_position,
        }
