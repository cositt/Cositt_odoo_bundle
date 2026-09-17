/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { titleService } from "@web/core/browser/title_service";
import { session } from "@web/session";

// Config ya viene embebida en el HTML de arranque (odoo.__session_info__)
// — cero RPC adicional. Ver models/ir_http.py.
//
// El <title> server-side (ver views/webclient_templates.xml) solo
// cubre la carga inicial y páginas sin JS (/web/login, portal): el
// backend es una SPA cuyo titleService recalcula document.title en
// CADA navegación (web/static/src/core/browser/title_service.js,
// updateTitle() hace `document.title = parts.join(" - ") || "Odoo"`,
// ignorando por completo el <title> servido) — sin este patch, el
// título de marca desaparecería en cuanto el usuario navegara a
// cualquier acción.
//
// patch() funciona igual sobre un objeto plano exportado
// (titleService) que sobre un prototipo de clase — verificado leyendo
// core/utils/patch.js antes de escribir esto (super.start(...) es
// válido en ambos casos). Se envuelve setParts() para que SIEMPRE
// incluya la marca como una parte más del título, en vez de tocar
// updateTitle() directamente (función interna, no expuesta, no
// parcheable).
const brand = session.cositt_browser_title;
if (brand) {
    patch(titleService, {
        start() {
            const service = super.start(...arguments);
            const originalSetParts = service.setParts;
            // Dos llamadas, no una: JS conserva el ORDEN DE INSERCIÓN
            // de las claves de un objeto, y setParts() actualiza el
            // valor de una clave ya existente sin mover su posición
            // (bug real encontrado en verificación manual: con una
            // sola llamada del estilo `{...parts, cositt_brand: brand}`,
            // la primera vez que se ejecuta (al arrancar, con parts
            // vacío) inserta cositt_brand ya como PRIMERA clave, y se
            // queda ahí para siempre — el título salía "Cositt ERP -
            // Inventory Overview" en vez de "Inventory Overview -
            // Cositt ERP"). Fix: en cada llamada, primero se BORRA la
            // clave (val falsy → delete, ver title_service.js) y
            // luego se vuelve a insertar — así siempre queda la
            // ÚLTIMA clave, y el nombre de la marca aparece al final,
            // detrás del nombre de la vista actual, como es
            // convención.
            service.setParts = (parts) => {
                originalSetParts({ ...parts, cositt_brand: false });
                originalSetParts({ cositt_brand: brand });
            };
            // Aplica de inmediato: cubre el Home Menu (sin acción
            // abierta, sin partes propias) donde, de otro modo,
            // document.title se quedaría en el "Odoo" hardcodeado.
            service.setParts({});
            return service;
        },
    });
}
