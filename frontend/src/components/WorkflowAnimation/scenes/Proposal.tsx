/**
 * Scene 6 — Proposal (frames 0-125 within this Sequence, starts at 605 globally)
 *
 * Left: step label + export format badges (docx, pdf, Notion) + timer badge.
 * Right: document frame with text lines streaming in — simulating Claude
 *        writing the proposal section by section via python-docx.
 */

import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FileText, Download, FileDown, BookOpen } from "lucide-react";
import { C, displayFont, bodyFont } from "../constants";

// Document lines — heading rows are taller + darker, body rows are lighter bars
const DOC_LINES = [
  { width: 0.60, height: 13, color: C.ink,     delay: 17, gap: 0  },  // H1
  { width: 0.40, height: 8,  color: C.smoke,   delay: 26, gap: 0  },  // subline
  { width: 1.00, height: 1,  color: C.mist,    delay: 34, gap: 6  },  // divider
  { width: 0.50, height: 11, color: C.ink,     delay: 42, gap: 8  },  // H2
  { width: 0.93, height: 7,  color: "#c5cad4", delay: 50, gap: 0  },
  { width: 0.86, height: 7,  color: "#c5cad4", delay: 55, gap: 0  },
  { width: 0.72, height: 7,  color: "#c5cad4", delay: 60, gap: 0  },
  { width: 0.44, height: 11, color: C.ink,     delay: 67, gap: 10 },  // H2
  { width: 0.88, height: 7,  color: "#c5cad4", delay: 74, gap: 0  },
  { width: 0.78, height: 7,  color: "#c5cad4", delay: 79, gap: 0  },
  { width: 0.90, height: 7,  color: "#c5cad4", delay: 84, gap: 0  },
  { width: 0.65, height: 7,  color: "#c5cad4", delay: 89, gap: 0  },
  { width: 0.42, height: 11, color: C.ink,     delay: 96, gap: 10 },  // H2
  { width: 0.82, height: 7,  color: "#c5cad4", delay: 102, gap: 0 },
];

const EXPORT_FORMATS = [
  { icon: FileDown, label: ".docx",  color: "#2563eb" },
  { icon: FileText, label: ".pdf",   color: "#dc2626" },
  { icon: BookOpen, label: "Notion", color: "#1a1a1a" },
];

export function Proposal() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entranceOpacity = interpolate(frame, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exitOpacity     = interpolate(frame, [100, 125], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const sceneOpacity    = Math.min(entranceOpacity, exitOpacity);

  const labelY = interpolate(frame, [0, 20], [20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const docSpring  = spring({ frame: Math.max(0, frame - 7), fps, config: { damping: 20, stiffness: 100 } });
  const docScale   = interpolate(docSpring, [0, 1], [0.88, 1]);
  const docOpacity = interpolate(frame, [7, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const downloadOpacity = interpolate(frame, [100, 115], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const downloadY       = interpolate(frame, [100, 115], [10, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const exportOpacity = interpolate(frame, [18, 32], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: C.white,
        opacity: sceneOpacity,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px 80px",
        gap: 52,
      }}
    >
      {/* ── LEFT: Label + export options ────────────────────────────────── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 20, minWidth: 250 }}>
        <div style={{ opacity: entranceOpacity, transform: `translateY(${labelY}px)` }}>
          <p style={{ ...displayFont, fontSize: 11, fontWeight: 600, letterSpacing: "0.16em", textTransform: "uppercase" as const, color: C.accent, marginBottom: 8 }}>
            06 · Proposal
          </p>
          <p style={{ ...displayFont, fontSize: 26, fontWeight: 700, color: C.ink, letterSpacing: "-0.03em", lineHeight: 1.2 }}>
            Writing your proposal
          </p>
          <p style={{ ...bodyFont, fontSize: 12, color: C.smoke, marginTop: 8, lineHeight: 1.6 }}>
            Claude drafts section by section via the Proposal Agent.
          </p>
        </div>

        {/* File reference */}
        <div style={{ opacity: docOpacity, display: "flex", alignItems: "center", gap: 8 }}>
          <FileText size={15} color={C.accent} strokeWidth={1.5} />
          <span style={{ ...bodyFont, fontSize: 11, color: C.smoke }}>stripe.com_proposal.docx</span>
        </div>

        {/* Export format badges */}
        <div style={{ opacity: exportOpacity, display: "flex", flexDirection: "column", gap: 10 }}>
          <p style={{ ...displayFont, fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase" as const, color: C.smoke }}>
            Export formats
          </p>
          <div style={{ display: "flex", gap: 8 }}>
            {EXPORT_FORMATS.map(({ icon: Icon, label, color }) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  background: C.surface,
                  border: `1.5px solid ${C.mist}`,
                  borderRadius: 8,
                  padding: "7px 12px",
                }}
              >
                <Icon size={12} color={color} strokeWidth={2} />
                <span style={{ ...displayFont, fontSize: 11, fontWeight: 600, color: C.ink }}>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Download ready */}
        <div
          style={{
            opacity: downloadOpacity,
            transform: `translateY(${downloadY}px)`,
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            background: "#f0fdf4",
            border: `1.5px solid #bbf7d0`,
            borderRadius: 9999,
            padding: "9px 18px",
            width: "fit-content",
          }}
        >
          <Download size={13} color={C.green} strokeWidth={2} />
          <span style={{ ...displayFont, fontSize: 12, fontWeight: 600, color: C.green }}>Ready to download</span>
        </div>
      </div>

      {/* ── RIGHT: Document preview ──────────────────────────────────────── */}
      <div
        style={{
          opacity: docOpacity,
          transform: `scale(${docScale})`,
          transformOrigin: "center",
          flex: 1,
          maxWidth: 540,
          background: C.white,
          border: `1.5px solid ${C.mist}`,
          borderRadius: 16,
          padding: "24px 26px 28px",
          boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
          overflow: "hidden",
        }}
      >
        {/* Document header */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18, paddingBottom: 14, borderBottom: `1px solid ${C.mist}` }}>
          <div style={{ width: 26, height: 26, borderRadius: 6, background: C.ink, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <FileText size={12} color={C.white} strokeWidth={1.5} />
          </div>
          <div>
            <p style={{ ...displayFont, fontSize: 11, fontWeight: 700, color: C.ink }}>DivAi — Technical Proposal</p>
            <p style={{ ...bodyFont, fontSize: 9, color: C.smoke }}>Prepared for: stripe.com · {new Date().toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</p>
          </div>
        </div>

        {/* Streaming lines */}
        <div style={{ display: "flex", flexDirection: "column" }}>
          {DOC_LINES.map(({ width, height, color, delay, gap }, i) => {
            const lineWidth   = interpolate(frame, [delay, delay + 12], [0, width * 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            const lineOpacity = interpolate(frame, [delay, delay + 7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

            return (
              <div key={i} style={{ height, width: `${lineWidth}%`, background: color, borderRadius: height <= 1 ? 0 : 4, opacity: lineOpacity, marginTop: gap + 5 }} />
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
}
