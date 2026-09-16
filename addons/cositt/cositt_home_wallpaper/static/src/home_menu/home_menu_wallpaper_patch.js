/** @odoo-module **/

import { onMounted, onWillUnmount } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { HomeMenu } from "@web_enterprise/webclient/home_menu/home_menu";

// Config ya viene embebida en el HTML de arranque (odoo.__session_info__,
// leído síncronamente por web/session.js) — cero RPC, disponible antes
// del primer render de este componente. Ver models/ir_http.py.
const WALLPAPER_CONFIG = session.cositt_home_wallpaper || { enabled: false };

const FIT_TO_BACKGROUND_SIZE = {
    cover: "cover",
    contain: "contain",
    center: "auto",
    stretch: "100% 100%",
};

const POSITION_TO_BACKGROUND_POSITION = {
    center: "center center",
    top: "center top",
    bottom: "center bottom",
};

// patch() sobre el componente público HomeMenu de web_enterprise: mismo
// mecanismo que ya usa este bundle en cositt_list_preferences sobre
// ListRenderer, y que usa el propio Odoo en mail/chatter_patch.js. No se
// toca ninguna plantilla ni el DOM de otro componente: this.rootRef ya
// es un campo público de la clase (useRef("root") en home_menu.js),
// apuntando al único elemento raíz del Home Menu.
patch(HomeMenu.prototype, {
    setup() {
        super.setup();
        if (WALLPAPER_CONFIG.enabled) {
            // Aplicado en body (no en this.rootRef.el): el propio Home
            // Menu de Enterprise es transparente y deja ver el fondo
            // pintado en un ancestro (así es como el propio
            // home_menu_background.scss del core ya lo resuelve, sobre
            // body/.o_web_client). Se activa SOLO mientras este
            // componente está montado (onMounted/onWillUnmount) para
            // que nunca pueda quedarse pegado al navegar a otra
            // pantalla ni aparecer en el login (que nunca monta este
            // componente).
            onMounted(() => this._cosittApplyWallpaper());
            onWillUnmount(() => this._cosittRemoveWallpaper());
        }
    },

    _cosittApplyWallpaper() {
        const config = WALLPAPER_CONFIG;
        const body = document.body;
        body.classList.add("o_cositt_wallpaper_active");
        body.style.setProperty(
            "--cositt-wallpaper-image",
            config.image_url ? `url("${config.image_url}")` : "none"
        );
        body.style.setProperty("--cositt-wallpaper-color", config.color || "transparent");
        body.style.setProperty(
            "--cositt-wallpaper-fit",
            FIT_TO_BACKGROUND_SIZE[config.fit] || "cover"
        );
        body.style.setProperty(
            "--cositt-wallpaper-position",
            POSITION_TO_BACKGROUND_POSITION[config.position] || "center center"
        );
        body.style.setProperty("--cositt-wallpaper-blur", `${config.blur || 0}px`);
        body.style.setProperty("--cositt-wallpaper-overlay", (config.overlay || 0) / 100);
    },

    _cosittRemoveWallpaper() {
        document.body.classList.remove("o_cositt_wallpaper_active");
    },
});
