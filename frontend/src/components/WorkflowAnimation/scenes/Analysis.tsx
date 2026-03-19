/**
 * Scene 3 — Analysis (frames 0-150 within this Sequence, starts at 255 globally)
 *
 * Central Cpu "brain" node with tech-stack chips radiating outward + dashed lines.
 * Below: an "Intelligence Report" card builds itself section by section,
 * showing what the Analysis Agent writes into DivAiState.intelligence_report.
 *
 * This represents Claude reading all the signals and classifying the tech stack,
 * API patterns, business model, and key technical risks.
 */

import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Cpu, Code2, CreditCard, Server, Database, Plug, FileSearch } from "lucide-react";
import { C, displayFont, bodyFont, COMP_W, COMP_H } from "../constants";

const CX = COMP_W / 2;
const CY = COMP_H / 2 - 30;

const CHIPS = [
  { icon: Code2,      label: "React 18",   color: "#61DAFB", bg: "#e0f7ff", x: CX - 275, y: CY - 90,  delay: 28 },
  { icon: CreditCard, label: "Stripe API", color: "#635BFF", bg: "#eeedff", x: CX - 195, y: CY + 90,  delay: 42 },
  { icon: Server,     label: "Node.js",    color: "#339933", bg: "#e6f5e6", x: CX,        y: CY - 160, delay: 35 },
  { icon: Database,   label: "PostgreSQL", color: "#336791", bg: "#e5eef7", x: CX + 195,  y: CY + 90,  delay: 53 },
  { icon: Plug,       label: "REST API",   color: "#f97316", bg: "#fff4ec", x: CX + 275,  y: CY - 90,  delay: 62 },
] as const;

const CHIP_W = 148;
const CHIP_H = 44;

// Intelligence report sections that build up in the bottom panel
const REPORT_FIELDS = [
  { label: "Tech stack",     value: "React 18 · Node.js · PostgreSQL · Stripe",  delay: 70 },
  { label: "Business model", value: "SaaS · subscription billing · API-first",   delay: 85 },
  { label: "Key APIs",       value: "Stripe Billing, Connect, Webhooks",          delay: 100 },
  { label: "Auth pattern",   value: "OAuth 2.0 · JWT sessions · CSRF tokens",     delay: 115 },
];

export function Analysis() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entranceOpacity = interpolate(frame, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exitOpacity     = interpolate(frame, [125, 150], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const sceneOpacity    = Math.min(entranceOpacity, exitOpacity);

  const labelY = interpolate(frame, [0, 20], [20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const brainSpring = spring({ frame: Math.max(0, frame - 7), fps, config: { damping: 14, stiffness: 80 } });
  const brainScale  = interpolate(brainSpring, [0, 1], [0, 1]);
  const glowSize    = interpolate(Math.sin(frame * 0.07), [-1, 1], [16, 30]);

  const linesOpacity = interpolate(frame, [35, 65], [0, 0.35], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Intelligence report panel slides up from bottom
  const reportOpacity = interpolate(frame, [65, 78], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const reportY       = interpolate(frame, [65, 78], [16, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: C.white, opacity: sceneOpacity }}>

      {/* ── Connecting lines ─────────────────────────────────────────────── */}
      <svg style={{ position: "absolute", inset: 0, pointerEvents: "none" }} width={COMP_W} height={COMP_H}>
        {CHIPS.map((chip) => (
          <line
            key={chip.label}
            x1={CX} y1={CY}
            x2={chip.x + CHIP_W / 2} y2={chip.y + CHIP_H / 2}
            stroke={C.accent}
            strokeWidth={1.5}
            strokeOpacity={linesOpacity}
            strokeDasharray="5 5"
          />
        ))}
      </svg>

      {/* ── Step label (top-centre) ──────────────────────────────────────── */}
      <div style={{ position: "absolute", top: 36, left: 0, right: 0, textAlign: "center", opacity: entranceOpacity, transform: `translateY(${labelY}px)` }}>
        <p style={{ ...displayFont, fontSize: 11, fontWeight: 600, letterSpacing: "0.16em", textTransform: "uppercase" as const, color: C.accent, marginBottom: 8 }}>
          03 · Analysis
        </p>
        <p style={{ ...displayFont, fontSize: 26, fontWeight: 700, color: C.ink, letterSpacing: "-0.03em" }}>
          Stack decoded by Claude
        </p>
      </div>

      {/* ── Central brain node ──────────────────────────────────────────── */}
      <div style={{ position: "absolute", left: CX - 36, top: CY - 36, width: 72, height: 72, transform: `scale(${brainScale})`, transformOrigin: "center" }}>
        <div style={{ position: "absolute", inset: -(glowSize / 2), borderRadius: "50%", background: `${C.accent}12`, border: `1px solid ${C.accent}22` }} />
        <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: C.ink, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Cpu size={28} color={C.white} strokeWidth={1.5} />
        </div>
      </div>

      {/* ── Tech chips ──────────────────────────────────────────────────── */}
      {CHIPS.map(({ icon: Icon, label, color, bg, x, y, delay }) => {
        const chipSpring  = spring({ frame: Math.max(0, frame - delay), fps, config: { damping: 20, stiffness: 110 } });
        const chipOpacity = interpolate(frame, [delay, delay + 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const chipScale   = interpolate(chipSpring, [0, 1], [0.7, 1]);

        return (
          <div
            key={label}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: CHIP_W,
              height: CHIP_H,
              opacity: chipOpacity,
              transform: `scale(${chipScale})`,
              transformOrigin: "center",
              display: "flex",
              alignItems: "center",
              gap: 10,
              background: bg,
              border: `1.5px solid ${color}30`,
              borderRadius: 10,
              padding: "0 14px",
            }}
          >
            <Icon size={14} color={color} strokeWidth={2} />
            <span style={{ ...bodyFont, fontSize: 12, fontWeight: 600, color: C.ink, whiteSpace: "nowrap" as const }}>{label}</span>
          </div>
        );
      })}

      {/* ── Intelligence report panel (bottom strip) ─────────────────────── */}
      <div
        style={{
          position: "absolute",
          bottom: 28,
          left: 80,
          right: 80,
          opacity: reportOpacity,
          transform: `translateY(${reportY}px)`,
          background: C.surface,
          border: `1.5px solid ${C.mist}`,
          borderRadius: 14,
          padding: "14px 20px",
          display: "flex",
          alignItems: "center",
          gap: 24,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
          <FileSearch size={15} color={C.accent} strokeWidth={1.8} />
          <span style={{ ...displayFont, fontSize: 11, fontWeight: 700, color: C.accent, letterSpacing: "0.06em", textTransform: "uppercase" as const }}>
            Intelligence Report
          </span>
        </div>
        <div style={{ width: 1, height: 28, background: C.mist, flexShrink: 0 }} />
        <div style={{ display: "flex", gap: 28, flex: 1, flexWrap: "wrap" as const }}>
          {REPORT_FIELDS.map(({ label, value, delay }) => {
            const fieldOpacity = interpolate(frame, [delay, delay + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return (
              <div key={label} style={{ opacity: fieldOpacity }}>
                <p style={{ ...displayFont, fontSize: 9, fontWeight: 600, color: C.smoke, textTransform: "uppercase" as const, letterSpacing: "0.1em", marginBottom: 2 }}>{label}</p>
                <p style={{ ...bodyFont, fontSize: 11, color: C.ink, fontWeight: 500 }}>{value}</p>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
}
