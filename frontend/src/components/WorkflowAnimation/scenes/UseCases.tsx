/**
 * Scene 4 — Use Cases (frames 0-140 within this Sequence, starts at 380 globally)
 *
 * Three opportunity cards spring in with staggered timing.
 * A RAG vector-search indicator shows how these were found — the Use Case Agent
 * queries ChromaDB with the intelligence report as the embedding input,
 * and retrieves the closest matching business opportunity patterns.
 */

import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Lightbulb, BarChart2, Layers, Database, Sparkles } from "lucide-react";
import { C, displayFont, bodyFont } from "../constants";

const USE_CASES = [
  {
    rank: "01", icon: Lightbulb,
    title: "Customer Portal Modernisation",
    detail: "Replace legacy PHP dashboard with React + API layer",
    score: 94, color: "#2563eb", delay: 20,
  },
  {
    rank: "02", icon: BarChart2,
    title: "AI Invoice Processing",
    detail: "Automate Stripe billing reconciliation with Claude",
    score: 87, color: "#7c3aed", delay: 40,
  },
  {
    rank: "03", icon: Layers,
    title: "Real-time Analytics Dashboard",
    detail: "Replace static reports with live WebSocket event stream",
    score: 81, color: "#059669", delay: 60,
  },
] as const;

export function UseCases() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entranceOpacity = interpolate(frame, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exitOpacity     = interpolate(frame, [115, 140], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const sceneOpacity    = Math.min(entranceOpacity, exitOpacity);

  const labelY = interpolate(frame, [0, 22], [20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // RAG indicator pops in with the label
  const ragOpacity = interpolate(frame, [10, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: C.white,
        opacity: sceneOpacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 80px",
        gap: 24,
      }}
    >
      {/* ── Header row ──────────────────────────────────────────────────── */}
      <div
        style={{
          opacity: entranceOpacity,
          transform: `translateY(${labelY}px)`,
          width: "100%",
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
        }}
      >
        <div>
          <p style={{ ...displayFont, fontSize: 11, fontWeight: 600, letterSpacing: "0.16em", textTransform: "uppercase" as const, color: C.accent, marginBottom: 8 }}>
            04 · Use Cases
          </p>
          <p style={{ ...displayFont, fontSize: 26, fontWeight: 700, color: C.ink, letterSpacing: "-0.03em" }}>
            3 opportunities identified
          </p>
        </div>

        {/* RAG retrieval badge */}
        <div
          style={{
            opacity: ragOpacity,
            display: "flex",
            alignItems: "center",
            gap: 8,
            background: C.surface,
            border: `1.5px solid ${C.mist}`,
            borderRadius: 10,
            padding: "9px 16px",
          }}
        >
          <Database size={12} color={C.smoke} strokeWidth={2} />
          <span style={{ ...bodyFont, fontSize: 11, color: C.smoke }}>ChromaDB</span>
          <div style={{ width: 1, height: 14, background: C.mist }} />
          <span style={{ ...bodyFont, fontSize: 11, color: C.accent, fontWeight: 600 }}>RAG retrieval</span>
          <span style={{ ...bodyFont, fontSize: 11, color: C.smoke }}>· 340 patterns searched</span>
        </div>
      </div>

      {/* ── Cards ───────────────────────────────────────────────────────── */}
      <div style={{ display: "flex", gap: 16, width: "100%" }}>
        {USE_CASES.map(({ rank, icon: Icon, title, detail, score, color, delay }) => {
          const cardSpring  = spring({ frame: Math.max(0, frame - delay), fps, config: { damping: 22, stiffness: 130 } });
          const cardOpacity = interpolate(frame, [delay, delay + 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const cardY       = interpolate(cardSpring, [0, 1], [44, 0]);
          const barWidth    = interpolate(frame, [delay + 28, delay + 60], [0, score], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

          return (
            <div
              key={rank}
              style={{
                flex: 1,
                opacity: cardOpacity,
                transform: `translateY(${cardY}px)`,
                background: C.white,
                border: `1.5px solid ${C.mist}`,
                borderRadius: 16,
                padding: "20px 20px",
                display: "flex",
                flexDirection: "column",
                gap: 14,
                boxShadow: "0 1px 6px rgba(0,0,0,0.05)",
              }}
            >
              {/* Rank + icon */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ ...displayFont, fontSize: 11, fontWeight: 700, letterSpacing: "0.12em", color: C.smoke }}>{rank}</span>
                <div style={{ width: 32, height: 32, borderRadius: 8, background: `${color}12`, border: `1.5px solid ${color}25`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Icon size={14} color={color} strokeWidth={2} />
                </div>
              </div>

              {/* Title + detail */}
              <div>
                <p style={{ ...displayFont, fontSize: 13, fontWeight: 700, color: C.ink, letterSpacing: "-0.01em", lineHeight: 1.3 }}>{title}</p>
                <p style={{ ...bodyFont, fontSize: 11, color: C.smoke, marginTop: 5, lineHeight: 1.5 }}>{detail}</p>
              </div>

              {/* Confidence score */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span style={{ ...bodyFont, fontSize: 10, color: C.smoke }}>Relevance match</span>
                  <span style={{ ...displayFont, fontSize: 11, fontWeight: 700, color }}>{Math.round(barWidth)}%</span>
                </div>
                <div style={{ height: 4, background: C.mist, borderRadius: 99 }}>
                  <div style={{ height: "100%", width: `${barWidth}%`, background: color, borderRadius: 99 }} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}
