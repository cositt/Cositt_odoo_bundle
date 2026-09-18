/** @odoo-module **/

import { session } from "@web/session";
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { getSeasonalTheme } from "./theme_data";

// Config ya viene embebida en el HTML de arranque (odoo.__session_info__)
// — cero RPC adicional. Ver models/ir_http.py. Se registra como ítem de
// systray (mismo mecanismo que Mensajes/Actividades/Usuario) en vez de
// un elemento position:fixed propio: evita competir por cualquier
// esquina de la pantalla ya ocupada por UI nativa (el indicador de
// "Loading" vive fijo en la esquina inferior derecha, las notificaciones
// en la superior derecha, y el breadcrumb/botones de cada vista ocupan
// la izquierda justo debajo del navbar — investigado en el core antes
// de elegir esta posición).
const config = session.cositt_seasonal_theme;

export class SeasonalThemeSystrayIcon extends Component {
    static template = "cositt_seasonal_theme.SystrayIcon";
    static props = {};

    setup() {
        this.config = config;
        this.theme = getSeasonalTheme(config.kind);
    }

    get tooltip() {
        return this.config.label || this.theme.defaultLabel;
    }
}

if (config) {
    registry.category("systray").add("cositt.seasonal_theme", {
        Component: SeasonalThemeSystrayIcon,
    }, { sequence: 1 });
}
