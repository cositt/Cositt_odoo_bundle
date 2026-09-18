/** @odoo-module **/

import { session } from "@web/session";
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { getSeasonalTheme } from "./theme_data";

// Solo se registra cuando hay tema activo Y el admin dejó las
// partículas encendidas — evita un componente vacío montado en el caso
// común (tema desactivado, o activado pero sin animación).
const config = session.cositt_seasonal_theme;

const CUSTOM_DOT_COLORS = ["#e74c3c", "#f1c40f", "#2ecc71", "#3498db", "#9b59b6", "#e67e22"];

function randomBetween(min, max) {
    return min + Math.random() * (max - min);
}

function pickRandom(list) {
    return list[Math.floor(Math.random() * list.length)];
}

export class SeasonalThemeParticles extends Component {
    static template = "cositt_seasonal_theme.Particles";
    static props = {};

    setup() {
        this.theme = getSeasonalTheme(config.kind);
        // Posiciones/tiempos generados una sola vez al montar, no por
        // fotograma — el movimiento real lo hace CSS (@keyframes), este
        // componente solo decide DÓNDE empieza cada partícula.
        this.particles = this._buildParticles();
    }

    particleStyle(particle) {
        return particle.color ? `${particle.style} background-color:${particle.color};` : particle.style;
    }

    _buildParticles() {
        const particles = [];
        for (const group of this.theme.particleGroups) {
            for (let i = 0; i < group.count; i++) {
                const isDot = !group.symbols;
                particles.push({
                    symbol: isDot ? null : pickRandom(group.symbols),
                    color: isDot ? pickRandom(CUSTOM_DOT_COLORS) : null,
                    kind: isDot ? "dot" : "emoji",
                    motion: group.motion,
                    style: this._buildStyle(group.motion),
                });
            }
        }
        return particles;
    }

    _buildStyle(motion) {
        const left = randomBetween(0, 100).toFixed(2);
        if (motion === "pop") {
            const top = randomBetween(5, 90).toFixed(2);
            const delay = randomBetween(0, 6).toFixed(2);
            const duration = randomBetween(2.5, 4.5).toFixed(2);
            return `left:${left}%; top:${top}%; animation-delay:${delay}s; animation-duration:${duration}s;`;
        }
        const delay = randomBetween(0, 10).toFixed(2);
        const duration = randomBetween(7, 14).toFixed(2);
        const drift = randomBetween(-40, 40).toFixed(0);
        return `left:${left}%; animation-delay:${delay}s; animation-duration:${duration}s; --cositt-seasonal-drift:${drift}px;`;
    }
}

if (config && config.animation_enabled) {
    registry.category("main_components").add("cositt.SeasonalThemeParticles", {
        Component: SeasonalThemeParticles,
    });
}
