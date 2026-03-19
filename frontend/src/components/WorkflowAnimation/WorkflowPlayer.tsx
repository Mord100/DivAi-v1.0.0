/**
 * WorkflowPlayer — the actual Remotion Player component.
 *
 * WHY this is a separate file from index.tsx:
 * Next.js dynamic() with { ssr: false } must wrap the entire module that
 * imports browser-only code. @remotion/player imports requestAnimationFrame
 * and other browser APIs at module level — they'd crash during server-side
 * rendering. By isolating the Player import here, index.tsx can safely
 * dynamic-import this file without the SSR constraint spreading further.
 *
 * CONCEPT: @remotion/player vs rendering to video
 * -------------------------------------------------
 * When you run `npx remotion render`, Remotion takes screenshots of every
 * frame and stitches them into an MP4. The <Player> component does the
 * opposite: it renders your composition directly in the browser DOM, frame
 * by frame, using requestAnimationFrame. No video file needed — it's just
 * a React component that plays your composition like a looping animation.
 */

"use client";

import { Player } from "@remotion/player";
import { WorkflowComposition } from "./Composition";
import { COMP_W, COMP_H, TOTAL_FRAMES, FPS } from "./constants";
import { ArrowUp } from "lucide-react";

interface Props {
  onStart: () => void;
}

export default function WorkflowPlayer({ onStart }: Props) {
  return (
    <div className="flex flex-col items-center gap-8">
      {/* ── Animation canvas ─────────────────────────────────────────────
          aspect-[2/1] locks the container to the composition's 2:1 ratio,
          so the Player fills it correctly at any screen width.            */}
      <div className="w-full aspect-[2/1] overflow-hidden rounded-2xl border border-neutral-200 shadow-sm bg-white">
        <Player
          component={WorkflowComposition}
          durationInFrames={TOTAL_FRAMES}
          compositionWidth={COMP_W}
          compositionHeight={COMP_H}
          fps={FPS}
          loop
          autoPlay
          // Prevent accidental pause on click — this is a showcase, not a scrubber
          clickToPlay={false}
          // Hide the default controls bar
          controls={false}
          style={{ width: "100%", height: "100%" }}
        />
      </div>

      {/* ── CTA button ───────────────────────────────────────────────────
          Lives outside the Player so it can handle real click events.
          Clicking scrolls smoothly back up to the hero URL form.         */}
      <button
        onClick={onStart}
        className="
          inline-flex items-center gap-2.5
          rounded-full bg-neutral-950 px-8 py-4
          text-sm font-semibold text-white
          hover:bg-neutral-700 active:scale-95
          transition-all duration-200
        "
      >
        <ArrowUp className="h-4 w-4" />
        Try it — analyse a site
      </button>
    </div>
  );
}
