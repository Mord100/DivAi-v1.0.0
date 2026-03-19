/**
 * Brand constants for Remotion scenes.
 *
 * WHY separate file: Remotion renders inside its own React tree with inline
 * styles — Tailwind classes don't apply inside the Player canvas. We mirror
 * the brand tokens from globals.css/brand.ts here as plain JS objects so
 * every scene shares the same design language without duplication.
 */

export const C = {
  ink:         "#0a0a0a",   // Primary dark — headings, borders
  accent:      "#2563eb",   // Blue — CTAs, highlights, active states
  accentLight: "#dbeafe",   // Blue tint — chip backgrounds
  white:       "#ffffff",   // Canvas background
  surface:     "#f8f9fa",   // Slightly off-white — cards, inputs
  mist:        "#e5e7eb",   // Borders, dividers
  smoke:       "#6b7280",   // Secondary text
  green:       "#16a34a",   // Success
} as const;

/** Display font style — mirrors the .font-display utility in globals.css */
export const displayFont: React.CSSProperties = {
  fontFamily: '"Mona Sans", ui-sans-serif, system-ui, sans-serif',
  fontVariationSettings: '"wdth" 125',
};

/** Body font style */
export const bodyFont: React.CSSProperties = {
  fontFamily: '"Mona Sans", ui-sans-serif, system-ui, sans-serif',
};

/** Mono font — used for the URL bar */
export const monoFont: React.CSSProperties = {
  fontFamily: '"SF Mono", "Fira Code", "Cascadia Code", monospace',
};

/**
 * Composition dimensions — drives the Player's aspect ratio.
 * 1280×640 = exactly 2:1, wide and cinematic.
 */
export const COMP_W = 1280;
export const COMP_H = 640;

/**
 * 770 frames @ 30fps = 25.7 seconds per loop.
 * Deliberately unhurried — each scene has room to breathe.
 */
export const TOTAL_FRAMES = 770;
export const FPS = 30;
