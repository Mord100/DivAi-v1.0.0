/**
 * WorkflowComposition — Root Remotion composition.
 *
 * 7 scenes totalling 770 frames @ 30fps = 25.7 seconds per loop.
 * Each adjacent pair of scenes overlaps by ~25 frames so the outgoing
 * scene fades out while the incoming one fades in — crossfade effect.
 *
 * Full DivAi pipeline covered:
 *   01 URL Input    → user pastes the target URL
 *   02 Ingestion    → Playwright scrapes DOM, network, JS globals
 *   03 Analysis     → Claude classifies tech stack + writes intelligence report
 *   04 Use Cases    → Use Case Agent RAG-retrieves ranked opportunities
 *   05 Solution     → Solution Agent matches blueprints from ChromaDB
 *   06 Proposal     → Proposal Agent writes the .docx via python-docx
 *   07 Complete     → Full agent pipeline graph + "Proposal ready"
 */

import { AbsoluteFill, Sequence } from "remotion";
import { UrlInput }  from "./scenes/UrlInput";
import { Ingestion } from "./scenes/Ingestion";
import { Analysis }  from "./scenes/Analysis";
import { UseCases }  from "./scenes/UseCases";
import { Solution }  from "./scenes/Solution";
import { Proposal }  from "./scenes/Proposal";
import { Complete }  from "./scenes/Complete";
import { C }         from "./constants";

export function WorkflowComposition() {
  return (
    <AbsoluteFill style={{ background: C.white }}>
      {/* 01 — URL Input:       0 → 140 */}
      <Sequence from={0} durationInFrames={140}>
        <UrlInput />
      </Sequence>

      {/* 02 — Ingestion:     115 → 280   (overlaps last 25 frames of UrlInput) */}
      <Sequence from={115} durationInFrames={165}>
        <Ingestion />
      </Sequence>

      {/* 03 — Analysis:      255 → 405   (overlaps last 25 frames of Ingestion) */}
      <Sequence from={255} durationInFrames={150}>
        <Analysis />
      </Sequence>

      {/* 04 — Use Cases:     380 → 520   (overlaps last 25 frames of Analysis) */}
      <Sequence from={380} durationInFrames={140}>
        <UseCases />
      </Sequence>

      {/* 05 — Solution:      495 → 630   (overlaps last 25 frames of UseCases) */}
      <Sequence from={495} durationInFrames={135}>
        <Solution />
      </Sequence>

      {/* 06 — Proposal:      605 → 730   (overlaps last 25 frames of Solution) */}
      <Sequence from={605} durationInFrames={125}>
        <Proposal />
      </Sequence>

      {/* 07 — Complete:      705 → 770   (overlaps last 25 frames of Proposal) */}
      <Sequence from={705} durationInFrames={65}>
        <Complete />
      </Sequence>
    </AbsoluteFill>
  );
}
