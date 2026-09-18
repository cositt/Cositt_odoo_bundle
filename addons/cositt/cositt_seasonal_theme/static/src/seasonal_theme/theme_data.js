/** @odoo-module **/

// Datos de presentación por tema — el servidor solo envía el "kind"
// (Selection validado por el ORM) más el mensaje/animación elegidos;
// icono, color y símbolos de partículas viven aquí porque son fijos
// por tema, no configurables. Total de partículas por tema acotado
// deliberadamente (≤20): "decoraciones ligeras", puro CSS, sin canvas
// ni bucle de JS por fotograma.
//
// Las claves deben coincidir con THEME_KINDS en
// models/res_company.py — si se agrega un tema en Python sin su
// entrada equivalente acá, getSeasonalTheme() cae en silencio a
// "christmas" (ver más abajo) en vez de fallar de forma visible.
export const SEASONAL_THEMES = {
    christmas: {
        icon: "🎄",
        defaultLabel: "¡Feliz Navidad!",
        particleGroups: [
            { symbols: ["❄️"], motion: "fall", count: 18 },
        ],
    },
    fair: {
        icon: "🎪",
        defaultLabel: "¡Feria en marcha!",
        particleGroups: [
            { symbols: ["🌸", "🌼", "🌻", "🌷"], motion: "fall", count: 14 },
        ],
    },
    birthday: {
        icon: "🎂",
        defaultLabel: "¡Feliz aniversario!",
        particleGroups: [
            { symbols: ["🕯️"], motion: "fall", count: 10 },
            { symbols: ["🎉", "✨"], motion: "pop", count: 10 },
        ],
    },
    custom: {
        icon: "🎊",
        defaultLabel: "Campaña especial",
        // symbols: null => partícula "punto de color" (ver particles.js),
        // no emoji — pedido explícito: "partículas de colores variados".
        particleGroups: [
            { symbols: null, motion: "fall", count: 20 },
        ],
    },
};

export function getSeasonalTheme(kind) {
    return SEASONAL_THEMES[kind] || SEASONAL_THEMES.christmas;
}
