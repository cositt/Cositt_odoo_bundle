/** @odoo-module **/

import { onWillStart } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useDebounced } from "@web/core/utils/timing";
import { ListRenderer } from "@web/views/list/list_renderer";

// Único punto de extensión usado: ListRenderer ya calcula y guarda las
// columnas opcionales activas en dos métodos concretos
// (computeOptionalActiveFields / saveOptionalActiveFields), pensados
// justo para esto — no hace falta tocar ninguna plantilla ni
// reimplementar la lista. Mismo mecanismo que usa el propio Odoo para
// extender componentes estándar (ver mail/chatter_patch.js).
patch(ListRenderer.prototype, {
    setup() {
        super.setup();
        this.cosittOrm = useService("orm");
        // Valor server-side cacheado en memoria del propio componente:
        // null mientras no se sabe (o no hay ninguna guardada) -> se
        // usa el valor de localStorage que ya calcula el core, sin
        // ningún cambio de comportamiento.
        this.cosittServerActiveFields = null;
        this.cosittSaveDebounced = useDebounced(this._cosittSavePreference, 400);

        const hasOptionalColumns = (this.props.archInfo.columns || []).some(
            (column) => column.optional
        );
        if (hasOptionalColumns) {
            onWillStart(async () => {
                try {
                    const value = await this.cosittOrm.call(
                        "cositt.list.column.preference",
                        "cositt_get_active_fields",
                        [this.keyOptionalFields]
                    );
                    if (value) {
                        this.cosittServerActiveFields = value.split(",");
                    }
                } catch {
                    // Sin red, sin permiso, vista todavía sin id (p.ej. una
                    // lista anidada muy dinámica)... nunca debe romper la
                    // lista: se sigue con el valor de localStorage de
                    // siempre, como si este módulo no existiera.
                    this.cosittServerActiveFields = null;
                }
            });
        }
    },

    computeOptionalActiveFields() {
        const optionalActiveFields = super.computeOptionalActiveFields();
        if (this.cosittServerActiveFields) {
            for (const fieldName of Object.keys(optionalActiveFields)) {
                optionalActiveFields[fieldName] = this.cosittServerActiveFields.includes(
                    fieldName
                );
            }
        }
        return optionalActiveFields;
    },

    saveOptionalActiveFields() {
        super.saveOptionalActiveFields();
        const activeFields = Object.keys(this.optionalActiveFields).filter(
            (fieldName) => this.optionalActiveFields[fieldName]
        );
        this.cosittServerActiveFields = activeFields;
        this.cosittSaveDebounced(this.keyOptionalFields, activeFields.join(","));
    },

    _cosittSavePreference(viewKey, activeFieldsCsv) {
        this.cosittOrm
            .call("cositt.list.column.preference", "cositt_set_active_fields", [
                viewKey,
                activeFieldsCsv,
            ])
            .catch(() => {
                // localStorage ya se actualizó en super.saveOptionalActiveFields();
                // si falla el guardado en servidor, la sesión actual sigue
                // funcionando con normalidad, solo no persiste entre
                // dispositivos esta vez.
            });
    },
});
