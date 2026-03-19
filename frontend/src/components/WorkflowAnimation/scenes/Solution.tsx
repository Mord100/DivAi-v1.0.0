/**
 * Scene 5 — Solution Matching (frames 0-135 within this Sequence, starts at 495 globally)
 *
 * The Solution Agent takes each use case and runs RAG against a library of
 * 200+ solution blueprints — finding the closest architectural pattern for each
 * opportunity and populating DivAiState.solutions.
 *
 * Visual layout:
 *   LEFT  — Agent context: "Solution Agent" label, ChromaDB blueprint library stats,
 *            and a mini LangGraph routing indicator showing we're in the Solution node
 *   RIGHT — 3 matched solution cards staggered in, each showing:
 *            - Blueprint name
 *            - Tech stack badges
 *            - Estimated timeline
 *            - Confidence score
 *
 * NEW CONCEPT: The LangGraph routing indicator
 * ---------------------------------------------
 * In DivAi's LangGraph graph, the Supervisor Agent decides which node runs next
 * based on the current DivAiState. The mini graph here shows:
 *   [Ingestion] → [Analysis] → [Use Cases] → [Solution] ← (you are here)
 * The active node is highlighted in blue. This gives a sense of where we are
 * in the stateful pipeline at any given moment.
 */

import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Wrench, Brain, BarChart2, Database, GitBranch, Clock, TrendingUp } from "lucide-react";
import { C, displayFont, bodyFont } from "../constants";

const BLUEPRINTS = [
  {
    rank: "01",
    icon: Wrench,
    name: "Modern SaaS Portal",
    stack: ["React 18", "Next.js", "tRPC", "PostgreSQL"],
    stackColors: ["#61DAFB", "#0a0a0a", "#398CCB", "#336791"],
    timeline: "6–8 weeks",
    match: 96,
    color: "#2563eb",
    delay: 22,
  },
  {
    rank: "02",
    icon: Brain,
    name: "AI Document Pipeline",
    stack: ["Claude API", "LangChain", "FastAPI", "Python"],
    stackColors: ["#d97706", "#34d399", "#009688", "#3572A5"],
    timeline: "3–4 weeks",
    match: 91,
    color: "#7c3aed",
    delay: 44,
  },
  {
    rank: "03",
    icon: BarChart2,
    name: "Analytics Platform",
    stack: ["React", "Recharts", "WebSocket", "Redis"],
    stackColors: ["#61DAFB", "#8b5cf6", "#f97316", "#cc0000"],
    timeline: "4–5 weeks",
    match: 83,
    color: "#059669",
    delay: 66,
  },
] as const;

// Mini pipeline node graph — shows where we are in the LangGraph
const PIPELINE_NODES = [
  { label: "Ingest",   active: false },
  { label: "Analyse",  active: false },
  { label: "Use Cases",active: false },
  { label: "Solution", active: true  }, // ← current node
  { label: "Proposal", active: false },
];

export function Solution() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entranceOpacity = interpolate(frame, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exitOpacity     = interpolate(frame, [110, 135], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const sceneOpacity    = Math.min(entranceOpacity, exitOpacity);

  const labelY = interpolate(frame, [0, 20], [20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const graphOpacity = interpolate(frame, [8, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const dbOpacity    = interpolate(frame, [14, 28], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: C.white,
        opacity: sceneOpacity,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        padding: "44px 72px 0",
        gap: 56,
      }}
    >
      {/* ── LEFT: Agent context panel ────────────────────────────────────── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 18, minWidth: 280, transform: `translateY(${labelY}px)` }}>
        {/* Step label */}
        <div style={{ opacity: entranceOpacity }}>
          <p style={{ ...displayFont, fontSize: 11, fontWeight: 600, letterSpacing: "0.16em", textTransform: "uppercase" as const, color: C.accent, marginBottom: 8 }}>
            05 · Solution Matching
          </p>
          <p style={{ ...displayFont, fontSize: 24, fontWeight: 700, color: C.ink, letterSpacing: "-0.03em", lineHeight: 1.2 }}>
            Blueprints retrieved
          </p>
          <p style={{ ...bodyFont, fontSize: 12, color: C.smoke, marginTop: 8, lineHeight: 1.6 }}>
            Solution Agent runs RAG against 247 architectural blueprints.
          </p>
        </div>

        {/* ChromaDB stats */}
        <div
          style={{
            opacity: dbOpacity,
            background: C.surface,
            border: `1.5px solid ${C.mist}`,
            borderRadius: 12,
            padding: "14px 16px",
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Database size={13} color={C.accent} strokeWidth={1.8} />
            <span style={{ ...displayFont, fontSize: 11, fontWeight: 600, color: C.ink }}>ChromaDB Vector Store</span>
          </div>
          <div style={{ display: "flex", gap: 16 }}>
            {[["247", "blueprints"], ["1,536", "dimensions"], ["cosine", "similarity"]].map(([val, lbl]) => (
              <div key={lbl}>
                <p style={{ ...displayFont, fontSize: 14, fontWeight: 700, color: C.ink }}>{val}</p>
                <p style={{ ...bodyFont, fontSize: 10, color: C.smoke }}>{lbl}</p>
              </div>
            ))}
          </div>
        </div>

        {/* LangGraph pipeline position */}
        <div style={{ opacity: graphOpacity }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
            <GitBranch size={11} color={C.smoke} strokeWidth={2} />
            <span style={{ ...displayFont, fontSize: 10, fontWeight: 600, color: C.smoke, letterSpacing: "0.1em", textTransform: "uppercase" as const }}>
              LangGraph · Agent position
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
            {PIPELINE_NODES.map((node, i) => (
              <div key={node.label} style={{ display: "flex", alignItems: "center" }}>
                <div
                  style={{
                    padding: "5px 9px",
                    borderRadius: 6,
                    background: node.active ? C.accent : C.surface,
                    border: `1.5px solid ${node.active ? C.accent : C.mist}`,
                    whiteSpace: "nowrap" as const,
                  }}
                >
                  <span style={{ ...displayFont, fontSize: 9, fontWeight: 700, color: node.active ? C.white : C.smoke }}>
                    {node.label}
                  </span>
                </div>
                {i < PIPELINE_NODES.length - 1 && (
                  <div style={{ width: 12, height: 1, background: C.mist }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── RIGHT: Blueprint cards ───────────────────────────────────────── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1 }}>
        <p style={{ ...displayFont, fontSize: 11, fontWeight: 600, letterSpacing: "0.12em", textTransform: "uppercase" as const, color: C.smoke, marginBottom: 4, opacity: entranceOpacity }}>
          Matched blueprints
        </p>

        {BLUEPRINTS.map(({ rank, icon: Icon, name, stack, stackColors, timeline, match, color, delay }) => {
          const cardSpring  = spring({ frame: Math.max(0, frame - delay), fps, config: { damping: 22, stiffness: 120 } });
          const cardOpacity = interpolate(frame, [delay, delay + 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const cardX       = interpolate(cardSpring, [0, 1], [36, 0]);
          const barWidth    = interpolate(frame, [delay + 24, delay + 55], [0, match], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

          return (
            <div
              key={rank}
              style={{
                opacity: cardOpacity,
                transform: `translateX(${cardX}px)`,
                background: C.white,
                border: `1.5px solid ${C.mist}`,
                borderRadius: 14,
                padding: "16px 18px",
                display: "flex",
                alignItems: "center",
                gap: 18,
                boxShadow: "0 1px 5px rgba(0,0,0,0.05)",
              }}
            >
              {/* Icon */}
              <div style={{ width: 38, height: 38, borderRadius: 9, background: `${color}10`, border: `1.5px solid ${color}22`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Icon size={16} color={color} strokeWidth={1.8} />
              </div>

              {/* Name + stack badges */}
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 7 }}>
                  <span style={{ ...displayFont, fontSize: 11, fontWeight: 700, color: C.smoke }}>{rank}</span>
                  <p style={{ ...displayFont, fontSize: 13, fontWeight: 700, color: C.ink }}>{name}</p>
                </div>
                <div style={{ display: "flex", gap: 5, flexWrap: "wrap" as const }}>
                  {stack.map((tech, i) => (
                    <span
                      key={tech}
                      style={{
                        ...bodyFont,
                        fontSize: 10,
                        fontWeight: 600,
                        color: stackColors[i],
                        background: `${stackColors[i]}12`,
                        border: `1px solid ${stackColors[i]}25`,
                        borderRadius: 5,
                        padding: "2px 7px",
                      }}
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>

              {/* Timeline + match */}
              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8, flexShrink: 0, minWidth: 110 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                  <Clock size={11} color={C.smoke} strokeWidth={2} />
                  <span style={{ ...bodyFont, fontSize: 11, color: C.smoke }}>{timeline}</span>
                </div>
                <div style={{ width: 110 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ ...bodyFont, fontSize: 9, color: C.smoke }}>Match</span>
                    <span style={{ ...displayFont, fontSize: 10, fontWeight: 700, color }}>{Math.round(barWidth)}%</span>
                  </div>
                  <div style={{ height: 3, background: C.mist, borderRadius: 99 }}>
                    <div style={{ height: "100%", width: `${barWidth}%`, background: color, borderRadius: 99 }} />
                  </div>
                </div>
                {/* High impact tag */}
                <div style={{ display: "flex", alignItems: "center", gap: 4, background: `${color}10`, borderRadius: 5, padding: "3px 8px" }}>
                  <TrendingUp size={9} color={color} strokeWidth={2} />
                  <span style={{ ...displayFont, fontSize: 9, fontWeight: 700, color }}>HIGH IMPACT</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}
