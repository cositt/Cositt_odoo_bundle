/** @odoo-module **/

import { session } from "@web/session";

// Config ya viene embebida en el HTML de arranque (odoo.__session_info__)
// — cero RPC adicional. Ver models/ir_http.py.
//
// Se fija en :root (document.documentElement), NO en un selector propio:
// backend_accent.scss consume esta variable reasignando las custom
// properties que Bootstrap y el navbar de Odoo YA exponen en tiempo de
// ejecución.
//
// La clase o_cositt_backend_accent_active es la parte que de verdad
// activa las reglas (ver backend_accent.scss para el porqué: un var()
// sin fallback NO es suficiente cuando se reasigna una custom property
// de Bootstrap a otra custom property — la regla entera tiene que
// dejar de existir en la cascada cuando está desactivado, no solo su
// valor). Bug real encontrado en verificación manual: sin esta clase,
// los botones primarios del backend quedaban invisibles por defecto.
const accentColor = session.cositt_backend_accent_color;
if (accentColor) {
    document.documentElement.classList.add("o_cositt_backend_accent_active");
    document.documentElement.style.setProperty("--cositt-backend-accent", accentColor);
}
