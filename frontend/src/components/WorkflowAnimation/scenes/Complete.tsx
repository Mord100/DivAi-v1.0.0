/**
 * Scene 7 — Complete (frames 0-65 within this Sequence, starts at 705 globally)
 *
 * Minimal success beat: CheckCircle springs in, "Proposal ready" text fades up,
 * timing badge follows. Short and clean — acts as a breath before the loop restarts.
 */

import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { CheckCircle2, Clock } from "lucide-react";
import { C, displayFont, bodyFont } from "../constants";

export function Complete() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sceneOpacity = interpolate(frame, [0, 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // CheckCircle springs in
  const checkSpring = spring({ frame: Math.max(0, frame - 3), fps, config: { damping: 12, stiffness: 90 } });
  const checkScale  = interpolate(checkSpring, [0, 1], [0, 1]);

  // Pulse ring expands and fades
  const pulseSpring  = spring({ frame: Math.max(0, frame - 6), fps, config: { damping: 10, stiffness: 40 } });
  const pulseScale   = interpolate(pulseSpring, [0, 1], [0.5, 2.4]);
  const pulseOpacity = interpolate(Math.max(0, frame - 6), [0, 8, 28], [0, 0.14, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const textOpacity = interpolate(frame, [16, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const textY       = interpolate(frame, [16, 26], [12, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const badgeOpacity = interpolate(frame, [26, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const badgeY       = interpolate(frame, [26, 36], [8, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: C.white,
        opacity: sceneOpacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 20,
      }}
    >
      {/* ── CheckCircle + pulse ring ──────────────────────────────────────── */}
      <div style={{ position: "relative", width: 72, height: 72, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: C.green, opacity: pulseOpacity, transform: `scale(${pulseScale})` }} />
        <div style={{ transform: `scale(${checkScale})`, position: "relative", zIndex: 1 }}>
          <CheckCircle2 size={66} color={C.green} strokeWidth={1.5} />
        </div>
      </div>

      {/* ── Text ─────────────────────────────────────────────────────────── */}
      <div style={{ opacity: textOpacity, transform: `translateY(${textY}px)`, textAlign: "center" as const }}>
        <p style={{ ...displayFont, fontSize: 34, fontWeight: 700, color: C.ink, letterSpacing: "-0.03em" }}>
          Proposal ready
        </p>
        <p style={{ ...bodyFont, fontSize: 13, color: C.smoke, marginTop: 6 }}>
          stripe.com — Technical Proposal v1
        </p>
      </div>

      {/* ── Timing badge ─────────────────────────────────────────────────── */}
      <div
        style={{
          opacity: badgeOpacity,
          transform: `translateY(${badgeY}px)`,
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          background: C.surface,
          border: `1.5px solid ${C.mist}`,
          borderRadius: 9999,
          padding: "9px 20px",
        }}
      >
        <Clock size={13} color={C.smoke} strokeWidth={2} />
        <span style={{ ...displayFont, fontSize: 12, fontWeight: 600, color: C.smoke }}>Generated in 4m 32s</span>
      </div>
    </AbsoluteFill>
  );
}
