/**
 * Scene 2 — Ingestion (frames 0-165 within this Sequence, starts at 115 globally)
 *
 * Split layout:
 *   LEFT  — Webpage wireframe with Playwright browser chrome + scan line sweep
 *   RIGHT — Extracted signals appearing one by one (DOM, JS, API, Auth)
 *           plus a live network traffic log streaming in at the bottom
 *
 * This represents the Playwright Ingestion Agent scraping the full DOM,
 * network traffic, JS globals, and tech fingerprints from the target URL.
 */

import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Network, Code2, Server, Lock, Scan, Activity } from "lucide-react";
import { C, displayFont, bodyFont, monoFont } from "../constants";

const SIGNALS = [
  { icon: Network,  label: "DOM structure",   sub: "2,847 nodes captured",   color: "#2563eb", delay: 25 },
  { icon: Code2,    label: "JS globals",      sub: "window.__stripe, __data", color: "#7c3aed", delay: 48 },
  { icon: Server,   label: "API endpoints",   sub: "12 XHR routes detected",  color: "#059669", delay: 70 },
  { icon: Lock,     label: "Auth patterns",   sub: "OAuth 2.0 · JWT · CSRF",  color: "#d97706", delay: 92 },
];

// Fake network log lines — simulate real-time request log
const LOG_LINES = [
  { text: "GET  /api/v1/customers    200  48ms",  delay: 55 },
  { text: "POST /api/v1/charges      201  120ms", delay: 68 },
  { text: "GET  /api/v1/subscriptions 200 31ms",  delay: 80 },
  { text: "GET  /api/v1/products     200  22ms",  delay: 90 },
  { text: "POST /api/v1/invoices     201  88ms",  delay: 100 },
];

export function Ingestion() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entranceOpacity = interpolate(frame, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exitOpacity     = interpolate(frame, [138, 165], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const sceneOpacity    = Math.min(entranceOpacity, exitOpacity);

  const labelY = interpolate(frame, [0, 22], [18, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const wireframeSpring  = spring({ frame: Math.max(0, frame - 12), fps, config: { damping: 20, stiffness: 90 } });
  const wireframeScale   = interpolate(wireframeSpring, [0, 1], [0.9, 1]);
  const wireframeOpacity = interpolate(frame, [12, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Scan line sweeps the 280px-tall wireframe content area
  const scanY       = interpolate(frame, [28, 105], [-5, 280], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const scanOpacity = interpolate(frame, [28, 38, 98, 105], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const badgeOpacity = interpolate(frame, [7, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: C.white,
        opacity: sceneOpacity,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        padding: "48px 72px 0",
        gap: 64,
      }}
    >
      {/* ── LEFT: Webpage wireframe ──────────────────────────────────────── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 18, transform: `translateY(${labelY}px)` }}>
        {/* Label */}
        <div style={{ opacity: entranceOpacity }}>
          <p style={{ ...displayFont, fontSize: 11, fontWeight: 600, letterSpacing: "0.16em", textTransform: "uppercase" as const, color: C.accent, marginBottom: 8 }}>
            02 · Scraping
          </p>
          <p style={{ ...displayFont, fontSize: 26, fontWeight: 700, color: C.ink, letterSpacing: "-0.03em" }}>
            Reading the page
          </p>
        </div>

        {/* Playwright badge */}
        <div style={{ opacity: badgeOpacity, display: "inline-flex", alignItems: "center", gap: 7, background: C.surface, border: `1.5px solid ${C.mist}`, borderRadius: 8, padding: "7px 14px", width: "fit-content" }}>
          <Scan size={12} color={C.accent} strokeWidth={2} />
          <span style={{ ...bodyFont, fontSize: 11, color: C.smoke, fontWeight: 500 }}>Playwright headless · Chromium</span>
        </div>

        {/* Webpage wireframe */}
        <div
          style={{
            position: "relative",
            opacity: wireframeOpacity,
            transform: `scale(${wireframeScale})`,
            transformOrigin: "top left",
            width: 270,
            background: C.white,
            border: `1.5px solid ${C.mist}`,
            borderRadius: 12,
            overflow: "hidden",
            boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
          }}
        >
          {/* Browser chrome */}
          <div style={{ background: "#f0f0f0", borderBottom: `1px solid ${C.mist}`, padding: "7px 12px", display: "flex", alignItems: "center", gap: 5 }}>
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#fc5c57" }} />
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#fdbc2c" }} />
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#34c84a" }} />
            <div style={{ flex: 1, height: 13, background: C.white, borderRadius: 4, marginLeft: 8, border: `1px solid ${C.mist}` }} />
          </div>
          {/* Page blocks */}
          <div style={{ padding: 12 }}>
            <div style={{ height: 32, background: C.ink, borderRadius: 5, marginBottom: 10 }} />
            <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
              <div style={{ flex: 2, height: 54, background: "#f3f4f6", borderRadius: 5 }} />
              <div style={{ flex: 1, height: 54, background: "#f3f4f6", borderRadius: 5 }} />
            </div>
            {[0.85, 0.7, 0.9, 0.55, 0.75].map((w, i) => (
              <div key={i} style={{ height: 7, width: `${w * 100}%`, background: C.mist, borderRadius: 3, marginBottom: 5 }} />
            ))}
            <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
              <div style={{ flex: 1, height: 22, background: C.accent, borderRadius: 4 }} />
              <div style={{ flex: 1, height: 22, background: "#f3f4f6", borderRadius: 4 }} />
            </div>
            <div style={{ height: 18, background: "#f3f4f6", borderRadius: 4, marginTop: 14 }} />
          </div>

          {/* Scan line */}
          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: 30 + scanY, // offset for chrome strip
              height: 2,
              background: `linear-gradient(90deg, transparent, ${C.accent}, transparent)`,
              opacity: scanOpacity,
              boxShadow: `0 0 14px 5px ${C.accent}50`,
            }}
          />
        </div>

        {/* Network log — streams in during scraping */}
        <div
          style={{
            width: 270,
            background: "#0f1117",
            border: `1px solid #1e2433`,
            borderRadius: 10,
            padding: "10px 12px",
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
            <Activity size={10} color="#4ade80" strokeWidth={2} />
            <span style={{ ...monoFont, fontSize: 9, color: "#4ade80", letterSpacing: "0.08em" }}>NETWORK LOG</span>
          </div>
          {LOG_LINES.map(({ text, delay: d }, i) => {
            const lineOpacity = interpolate(frame, [d, d + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return (
              <p key={i} style={{ ...monoFont, fontSize: 9, color: "#64748b", lineHeight: 1.7, opacity: lineOpacity, margin: 0 }}>
                {text}
              </p>
            );
          })}
        </div>
      </div>

      {/* ── RIGHT: Extracted signals ─────────────────────────────────────── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12, paddingTop: 58, minWidth: 330 }}>
        <p style={{ ...displayFont, fontSize: 11, fontWeight: 600, letterSpacing: "0.12em", textTransform: "uppercase" as const, color: C.smoke, marginBottom: 4 }}>
          Signals extracted
        </p>

        {SIGNALS.map(({ icon: Icon, label, sub, color, delay }) => {
          const itemSpring  = spring({ frame: Math.max(0, frame - delay), fps, config: { damping: 22, stiffness: 120 } });
          const itemOpacity = interpolate(frame, [delay, delay + 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const itemX       = interpolate(itemSpring, [0, 1], [44, 0]);

          return (
            <div
              key={label}
              style={{
                opacity: itemOpacity,
                transform: `translateX(${itemX}px)`,
                display: "flex",
                alignItems: "center",
                gap: 14,
                background: C.surface,
                border: `1.5px solid ${C.mist}`,
                borderRadius: 12,
                padding: "14px 18px",
              }}
            >
              <div style={{ width: 36, height: 36, borderRadius: "50%", background: `${color}12`, border: `1.5px solid ${color}28`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Icon size={16} color={color} strokeWidth={1.8} />
              </div>
              <div>
                <p style={{ ...displayFont, fontSize: 13, fontWeight: 600, color: C.ink }}>{label}</p>
                <p style={{ ...bodyFont, fontSize: 11, color: C.smoke, marginTop: 2 }}>{sub}</p>
              </div>
            </div>
          );
        })}

        {/* "Passing to Analysis Agent" handoff indicator */}
        {(() => {
          const handoffOpacity = interpolate(frame, [108, 122], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <div style={{ opacity: handoffOpacity, display: "flex", alignItems: "center", gap: 8, padding: "10px 14px", background: C.accentLight, border: `1.5px solid ${C.accent}30`, borderRadius: 10 }}>
              <div style={{ width: 7, height: 7, borderRadius: "50%", background: C.accent }} />
              <span style={{ ...bodyFont, fontSize: 11, color: C.accent, fontWeight: 600 }}>Handing off to Analysis Agent →</span>
            </div>
          );
        })()}
      </div>
    </AbsoluteFill>
  );
}
