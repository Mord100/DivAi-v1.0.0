/**
 * Scene 1 — URL Input (frames 0-140 within this Sequence)
 *
 * Browser address bar with URL typing in character by character.
 * A "Scan initiated" badge confirms the pipeline has started.
 */

import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Globe, Zap, ArrowRight } from "lucide-react";
import { C, displayFont, monoFont, bodyFont } from "../constants";

const TARGET_URL = "https://stripe.com";

export function UrlInput() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Exit fade (last 20 frames) ──────────────────────────────────────────
  const sceneOpacity = interpolate(frame, [120, 140], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Scene label slides up (frames 0-20) ────────────────────────────────
  const labelOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const labelY = interpolate(frame, [0, 20], [22, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Browser bar springs in (frames 12-32) ──────────────────────────────
  const barSpring = spring({ frame: Math.max(0, frame - 12), fps, config: { damping: 18, stiffness: 100 } });
  const barOpacity = interpolate(frame, [12, 32], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const barScale = interpolate(barSpring, [0, 1], [0.88, 1]);

  // ── URL typing (frames 32-100) ─────────────────────────────────────────
  const charsVisible = Math.floor(
    interpolate(frame, [32, 100], [0, TARGET_URL.length], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );
  const cursorOn = frame % 22 < 13 && charsVisible < TARGET_URL.length;

  // ── "Scan initiated" badge (frames 105-120) ────────────────────────────
  const badgeOpacity = interpolate(frame, [105, 120], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const badgeY = interpolate(frame, [105, 120], [14, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── "What happens next" hint (frames 112-128) ──────────────────────────
  const hintOpacity = interpolate(frame, [112, 126], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: C.white,
        opacity: sceneOpacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 28,
        padding: "0 120px",
      }}
    >
      {/* ── Step label ─────────────────────────────────────────────────── */}
      <div
        style={{
          opacity: labelOpacity,
          transform: `translateY(${labelY}px)`,
          textAlign: "center",
        }}
      >
        <p style={{ ...displayFont, fontSize: 11, fontWeight: 600, letterSpacing: "0.16em", textTransform: "uppercase" as const, color: C.accent, marginBottom: 10 }}>
          01 · Ingestion
        </p>
        <p style={{ ...displayFont, fontSize: 36, fontWeight: 700, color: C.ink, letterSpacing: "-0.03em", lineHeight: 1.1 }}>
          Target acquired
        </p>
      </div>

      {/* ── Browser address bar ────────────────────────────────────────── */}
      <div
        style={{
          opacity: barOpacity,
          transform: `scale(${barScale})`,
          width: 620,
          background: C.surface,
          border: `1.5px solid ${C.mist}`,
          borderRadius: 14,
          overflow: "hidden",
          boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
        }}
      >
        {/* macOS-style chrome strip */}
        <div style={{ background: "#f0f0f0", borderBottom: `1px solid ${C.mist}`, padding: "8px 14px", display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#fc5c57" }} />
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#fdbc2c" }} />
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#34c84a" }} />
        </div>
        {/* URL row */}
        <div style={{ padding: "14px 18px", display: "flex", alignItems: "center", gap: 12 }}>
          <Globe size={16} color={C.smoke} strokeWidth={1.5} />
          <span style={{ ...monoFont, fontSize: 15, color: C.ink, letterSpacing: "0.01em", flex: 1 }}>
            {TARGET_URL.slice(0, charsVisible)}
            {cursorOn && (
              <span style={{ display: "inline-block", width: 2, height: 15, background: C.accent, marginLeft: 1, verticalAlign: "middle" }} />
            )}
          </span>
          {/* Analyse button hint — appears after URL is typed */}
          {charsVisible >= TARGET_URL.length && (
            <div style={{ opacity: interpolate(frame, [102, 112], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }), display: "flex", alignItems: "center", gap: 6, background: C.accent, borderRadius: 8, padding: "6px 14px" }}>
              <span style={{ ...displayFont, fontSize: 11, fontWeight: 600, color: C.white }}>Analyse</span>
              <ArrowRight size={11} color={C.white} />
            </div>
          )}
        </div>
      </div>

      {/* ── Scan initiated badge ───────────────────────────────────────── */}
      <div
        style={{
          opacity: badgeOpacity,
          transform: `translateY(${badgeY}px)`,
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          background: C.accent,
          color: C.white,
          borderRadius: 9999,
          padding: "10px 24px",
          fontSize: 13,
          fontWeight: 600,
          letterSpacing: "0.04em",
          ...displayFont,
        }}
      >
        <Zap size={14} fill="white" color="white" />
        Scan initiated
      </div>

      {/* ── Pipeline hint ──────────────────────────────────────────────── */}
      <p style={{ ...bodyFont, fontSize: 12, color: C.smoke, opacity: hintOpacity, letterSpacing: "0.01em" }}>
        Launching Playwright · Analysis Agent · Use Case Agent · Proposal Agent
      </p>
    </AbsoluteFill>
  );
}
