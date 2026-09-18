/** @odoo-module **/

import { session } from "@web/session";
import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

// Config ya viene embebida en el HTML de arranque (odoo.__session_info__)
// — cero RPC adicional. Ver models/ir_http.py. Solo se registra el
// componente cuando hay algo que mostrar: evita un render vacío en el
// caso común (módulo instalado pero sin aviso configurado).
const config = session.cositt_announcement_banner;

const STYLE_CLASSES = {
    info: "alert-info",
    success: "alert-success",
    warning: "alert-warning",
    danger: "alert-danger",
};

export class AnnouncementBanner extends Component {
    static template = "cositt_announcement_banner.AnnouncementBanner";
    static props = {};

    setup() {
        this.config = config;
        this.state = useState({ dismissed: false });
        this.rootRef = useRef("root");
        this.resizeObserver = null;

        onMounted(() => {
            // El mensaje puede ocupar 1 o varias líneas según el ancho de
            // pantalla — se mide la altura real del banner y se empuja el
            // resto del backend con ese valor (ver .scss), en vez de asumir
            // una altura fija que dejaría un hueco o un solape con el navbar.
            document.documentElement.classList.add("o_cositt_announcement_banner_active");
            this.resizeObserver = new ResizeObserver(() => this._updateHeightVar());
            this.resizeObserver.observe(this.rootRef.el);
            this._updateHeightVar();
        });

        onWillUnmount(() => this._cleanup());
    }

    _updateHeightVar() {
        if (!this.rootRef.el) {
            return;
        }
        document.documentElement.style.setProperty(
            "--cositt-announcement-banner-height",
            `${this.rootRef.el.offsetHeight}px`
        );
    }

    _cleanup() {
        this.resizeObserver?.disconnect();
        document.documentElement.classList.remove("o_cositt_announcement_banner_active");
        document.documentElement.style.removeProperty("--cositt-announcement-banner-height");
    }

    get rootClass() {
        const styleClass = STYLE_CLASSES[this.config.style] || STYLE_CLASSES.info;
        return `o_cositt_announcement_banner alert mb-0 d-flex align-items-center justify-content-between ${styleClass}`;
    }

    dismiss() {
        this.state.dismissed = true;
        this._cleanup();
    }
}

if (config) {
    registry.category("main_components").add("cositt.AnnouncementBanner", {
        Component: AnnouncementBanner,
    });
}
