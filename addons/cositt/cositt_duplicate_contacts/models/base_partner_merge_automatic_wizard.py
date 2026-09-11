from odoo import api, fields, models


class BasePartnerMergeAutomaticWizard(models.TransientModel):
    _inherit = "base.partner.merge.automatic.wizard"

    # El asistente nativo ya detecta grupos "group_by_<campo>" de forma
    # genérica (ver _compute_selected_groupby/_generate_query en el core):
    # basta con añadir el campo para que aparezca como criterio de búsqueda,
    # sin tocar la lógica de fusión. Se usa phone_sanitized (ya normalizado
    # por Odoo, requiere el módulo phone_validation) en vez de "phone" a
    # secas para no depender del formato en que cada uno escribió el número.
    # String en inglés a propósito: es el mismo idioma que usan las etiquetas
    # nativas vecinas (Email, Name, VAT...) y así se traduce igual que ellas
    # según el idioma de cada instancia (ver i18n/es.po).
    group_by_phone_sanitized = fields.Boolean("Phone")

    @api.model
    def _generate_query(self, fields, maximum_group=100):
        # Override completo de base/wizard/base_partner_merge.py
        # (Odoo 19.0, método _generate_query) — no hay hook en el core para
        # extender solo la lista de NOT NULL, así que se copia entero.
        # Re-diffear este método contra el core en cada upgrade de Odoo.
        #
        # Cambios respecto al original:
        # 1) 'phone_sanitized' se añade a los campos que excluyen NULL del
        #    GROUP BY. El core solo lo hace para 'email'/'name'/'vat'
        #    (hardcoded); sin esto, agrupar por teléfono uniría en un único
        #    "grupo duplicado" a TODOS los contactos sin teléfono (SQL agrupa
        #    los NULL juntos), generando falsos positivos masivos.
        # 2) flush_all() antes de construir la consulta: phone_sanitized es
        #    un campo computado y almacenado, y esta consulta es SQL crudo
        #    (cr.execute) que no ve cambios pendientes de la misma
        #    transacción sin flush (verificado: sin esto, un contacto
        #    creado/editado justo antes no aparece con su teléfono).
        if "phone_sanitized" in fields:
            self.env.flush_all()

        sql_fields = []
        for field in fields:
            if field in ("email", "name"):
                sql_fields.append("lower(%s)" % field)
            elif field == "vat":
                sql_fields.append("replace(%s, ' ', '')" % field)
            else:
                sql_fields.append(field)
        group_fields = ", ".join(sql_fields)

        filters = []
        for field in fields:
            if field in ("email", "name", "vat", "phone_sanitized"):
                filters.append((field, "IS NOT", "NULL"))
        criteria = " AND ".join(
            "%s %s %s" % (field, operator, value) for field, operator, value in filters
        )

        text = ["SELECT min(id), array_agg(id)", "FROM res_partner"]
        if criteria:
            text.append("WHERE %s" % criteria)
        text.extend(
            [
                "GROUP BY %s" % group_fields,
                "HAVING COUNT(*) >= 2",
                "ORDER BY min(id)",
            ]
        )
        if maximum_group:
            text.append("LIMIT %s" % maximum_group)

        return " ".join(text)
