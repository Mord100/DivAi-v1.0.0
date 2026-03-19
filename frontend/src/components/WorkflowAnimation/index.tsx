/**
 * WorkflowAnimation — public export for the landing page.
 *
 * CONCEPT: Next.js dynamic() with ssr: false
 * -------------------------------------------
 * Next.js pre-renders pages on the server. Remotion uses browser APIs
 * (requestAnimationFrame, performance.now, etc.) that don't exist in Node.js.
 *
 * dynamic() is Next.js's code-splitting import. The { ssr: false } option
 * tells Next: "don't even try to render this on the server — only load it
 * in the browser after hydration."
 *
 * The loading fallback is a skeleton box matching the Player's aspect ratio,
 * so the page doesn't jump when the animation hydrates.
 */

"use client";

import dynamic from "next/dynamic";

// Load WorkflowPlayer only in the browser — never on the server
const WorkflowPlayer = dynamic(() => import("./WorkflowPlayer"), {
  ssr: false,
  loading: () => (
    // Skeleton placeholder — same aspect ratio as the Player so no layout shift
    <div className="w-full aspect-[2/1] rounded-2xl bg-neutral-100 animate-pulse" />
  ),
});

interface Props {
  /** Called when the user clicks the CTA — parent handles scrolling */
  onStart: () => void;
}

export function WorkflowAnimation({ onStart }: Props) {
  return <WorkflowPlayer onStart={onStart} />;
}
