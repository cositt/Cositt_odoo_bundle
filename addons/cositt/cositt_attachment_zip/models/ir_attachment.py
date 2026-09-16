import re
from collections import OrderedDict

from odoo import _, api, models
from odoo.exceptions import AccessError, UserError

UNSAFE_CHARS_RE = re.compile(r'[\\/:*?"<>|\n\r\t]')
MAX_COMPONENT_LENGTH = 150

# Límites documentados de la descarga ZIP (README): un worker de Odoo con
# la config por defecto tiene un límite de memoria de proceso (varios
# cientos de MB - unos pocos GB según --limit-memory-*); construir el ZIP
# implica tener en memoria a la vez el contenido crudo de cada adjunto más
# el propio buffer del ZIP, y el resultado final se guarda codificado en
# base64 en una columna del wizard (otro ~33% extra). Estos límites evitan
# que una selección enorme haga fallar (o degrade) un worker en silencio;
# si se superan, se avisa con un UserError claro en vez de intentarlo igual.
MAX_ATTACHMENT_COUNT = 300
MAX_TOTAL_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def cositt_action_open_attachment_zip_wizard(self):
        # Enganchada genéricamente a ir.attachment (Ajustes > Técnico >
        # Adjuntos): funciona igual para cualquier modelo de negocio sin
        # depender de sale/account/project, y sin sudo() en ningún punto
        # (mismo patrón que cositt_pdf_merge).
        if not self:
            raise UserError(_("Selecciona al menos un adjunto para descargar."))

        # Forzar lectura de un campo de cada adjunto: si el usuario no
        # tiene acceso a alguno (o a su registro padre), esto lanza
        # AccessError aquí mismo, antes de crear nada.
        self.mapped("name")

        wizard = self.env["cositt.attachment.zip.wizard"].create({
            "attachment_ids": [(6, 0, self.ids)],
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Descargar adjuntos (ZIP)"),
            "res_model": "cositt.attachment.zip.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.model
    def _cositt_sanitize_path_component(self, text, fallback):
        # Defensa contra "zip slip"/path traversal: ningún componente de
        # ruta que construyamos puede contener separadores de directorio
        # ni quedarse en algo compuesto solo de puntos (".", "..").
        text = (text or "").strip()
        text = UNSAFE_CHARS_RE.sub("_", text)
        text = text.strip(". ")
        text = text[:MAX_COMPONENT_LENGTH]
        return text or fallback

    @api.model
    def _cositt_dedupe_names(self, names):
        # Reutilizado tanto para nombres de carpeta como de archivo: si
        # "factura.pdf" se repite, la segunda aparición pasa a
        # "factura_2.pdf", la tercera a "factura_3.pdf", etc. Sin
        # depender de os.path (evita separadores propios del SO en la
        # extensión) para mantener el resultado 100% determinista.
        seen_count = {}
        used = set()
        result = []
        for name in names:
            if name not in seen_count:
                seen_count[name] = 0
            if name not in used:
                used.add(name)
                result.append(name)
                continue

            if "." in name:
                base, _dot, ext = name.rpartition(".")
                ext = "." + ext
            else:
                base, ext = name, ""

            seen_count[name] += 1
            candidate = "%s_%d%s" % (base, seen_count[name] + 1, ext)
            while candidate in used:
                seen_count[name] += 1
                candidate = "%s_%d%s" % (base, seen_count[name] + 1, ext)
            used.add(candidate)
            result.append(candidate)
        return result

    def _cositt_group_by_record(self):
        # Agrupa preservando el orden de selección original. Clave
        # (res_model, res_id); (False, False) para adjuntos huérfanos.
        groups = OrderedDict()
        for attachment in self:
            key = (attachment.res_model or False, attachment.res_id or False)
            groups.setdefault(key, self.browse())
            groups[key] |= attachment
        return groups

    def _cositt_folder_name_for(self, res_model, res_id):
        if not res_model or not res_id:
            return _("Sin registro vinculado")
        fallback = _("Registro #%s") % res_id
        try:
            record = self.env[res_model].browse(res_id)
            if not record.exists():
                return self._cositt_sanitize_path_component(
                    _("Registro eliminado %s") % res_id, fallback
                )
            name = record.display_name
        except (KeyError, AccessError):
            return self._cositt_sanitize_path_component(
                _("Registro sin acceso %s") % res_id, fallback
            )
        return self._cositt_sanitize_path_component(name, fallback)

    def _cositt_check_zip_limits(self):
        count = len(self)
        if count > MAX_ATTACHMENT_COUNT:
            raise UserError(
                _("Selecciona como máximo %(max)d adjuntos por descarga "
                  "ZIP (has seleccionado %(count)d). Reduce la selección "
                  "e inténtalo de nuevo.") % {
                    "max": MAX_ATTACHMENT_COUNT, "count": count,
                }
            )
        total_size = sum(self.mapped("file_size"))
        if total_size > MAX_TOTAL_SIZE_BYTES:
            raise UserError(
                _("El tamaño total de los adjuntos seleccionados (%(total)s) "
                  "supera el límite de %(limit)s por descarga ZIP. Reduce "
                  "la selección e inténtalo de nuevo.") % {
                    "total": self._cositt_human_size(total_size),
                    "limit": self._cositt_human_size(MAX_TOTAL_SIZE_BYTES),
                }
            )

    @api.model
    def _cositt_human_size(self, num_bytes):
        value = float(num_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024 or unit == "GB":
                return "%.1f %s" % (value, unit) if unit != "B" else "%d B" % value
            value /= 1024
        return "%.1f GB" % value
