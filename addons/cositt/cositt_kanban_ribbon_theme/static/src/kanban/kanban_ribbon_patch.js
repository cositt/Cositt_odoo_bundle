/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { getColorIndex, KanbanRecord } from "@web/views/kanban/kanban_record";

// Config ya viene embebida en el HTML de arranque (odoo.__session_info__)
// — cero RPC por vista kanban abierta. Ver models/ir_http.py.
const RIBBON_RULES = session.cositt_kanban_ribbon_rules || {};

// Reflejo 1:1 del Selection "style" del modelo (ver
// cositt_kanban_ribbon_rule.py) — "ribbon" mapeado a la clase histórica
// o_cositt_kanban_ribbon (sin renombrar, evita romper CSS ya escrito
// contra ese nombre en despliegues existentes de este módulo).
const STYLE_TO_CLASS = {
    ribbon: "o_cositt_kanban_ribbon",
    border: "o_cositt_kanban_border",
    dot: "o_cositt_kanban_dot",
};

// patch() sobre getRecordClasses(), NO sobre la plantilla OWL de
// KanbanRecord: es la misma función que el propio core ya usa para
// añadir o_kanban_color_N cuando el arch declara card_color_field
// (ver kanban_record.js) — reusarla en vez de heredar la plantilla
// mantiene este módulo inmune a cambios de markup entre versiones, y
// evita el mismo tipo de sorpresa que ya costó un rediseño completo en
// cositt_login_background (ahí sí hacía falta tocar plantillas server,
// porque el login no es un componente OWL; el kanban sí lo es y expone
// este método justamente para esto).
patch(KanbanRecord.prototype, {
    // getRecordClasses() devuelve un STRING ya unido (`classes.join(" ")`
    // en el core, no un array) — comprobado leyendo el código fuente
    // antes de escribir esto. Concatenar, no .push().
    getRecordClasses() {
        const baseClasses = super.getRecordClasses();
        const rule = RIBBON_RULES[this.props.record.resModel];
        if (!rule) {
            return baseClasses;
        }
        const value = this.props.record.data[rule.field];
        if (value === undefined) {
            return baseClasses;
        }
        // getColorIndex() hace `value % COLORS.length` con el operador
        // JS nativo, que conserva el signo del dividendo — un
        // color_field_name que apunte a un Integer legítimamente
        // negativo (no necesariamente el "color" nativo, cualquier
        // Integer del modelo) daría un índice negativo (ej. -3), y
        // "o_colorlist_item_color_-3" no coincide con ninguna regla
        // del @for de kanban_ribbon.scss (genera solo _1.._11) — el
        // ribbon quedaría invisible en vez de mostrar un color real.
        // Normalizado aquí a un módulo verdadero.
        const rawIndex = getColorIndex(value);
        const colorIndex = ((rawIndex % 12) + 12) % 12;
        if (colorIndex === 0) {
            // Índice 0 = "Sin color" en la paleta nativa (ver
            // ColorList.COLORS) — no pintar un indicador gris en TODAS
            // las tarjetas por defecto, solo en las que de verdad
            // tienen un color elegido.
            return baseClasses;
        }
        // Una clase por estilo (ribbon/border/dot, ver
        // kanban_ribbon.scss) + el mismo o_colorlist_item_color_N de
        // siempre para el color en sí — el estilo solo decide la
        // FORMA, nunca inventa una paleta nueva.
        const styleClass = STYLE_TO_CLASS[rule.style] || STYLE_TO_CLASS.ribbon;
        return `${baseClasses} ${styleClass} o_colorlist_item_color_${colorIndex}`;
    },
});
