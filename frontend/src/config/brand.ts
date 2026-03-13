/**
 * DivAi brand configuration.
 * Central place for identity values used across all pages.
 * Pattern adapted from the DiV Dynamics brand-starter kit.
 */
export const brand = {
  name: "DivAi",
  nameShort: "DIVAI",
  tagline: "Turn any website into a qualified lead.",
  description:
    "DivAi scrapes, analyses, and writes a full technical proposal for any website in under 5 minutes.",
  url: "divai.io",
  email: "hello@divai.io",
  year: new Date().getFullYear(),

  logo: {
    dark: "/logo.png",
    light: "/logo-inverted.png",
    brandmark: "/brandmark.png",
    width: 1600,
    height: 400,
  },

  palette: {
    ink:    "#0a0a0a",   // Primary — headers, dark surfaces
    accent: "#2563eb",   // Blue — CTAs, highlights
    white:  "#ffffff",   // Ground — content background
    smoke:  "#525252",   // Body copy
    mist:   "#d4d4d4",   // Borders, dividers
  },
};
