"use client";

import { use, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Container } from "@/components/Container";
import { FadeIn, FadeInStagger } from "@/components/FadeIn";
import { NodeCard } from "@/components/NodeCard";
import { UseCaseSelector } from "@/components/UseCaseSelector";
import { SolutionSelector } from "@/components/SolutionSelector";
import { useAgentStream } from "@/hooks/useAgentStream";
import { ArrowRight, Radio } from "lucide-react";

interface PageProps { params: Promise<{ sessionId: string }> }

// Determines the key for AnimatePresence so panels cross-fade cleanly
function rightPanelKey(
  isComplete: boolean,
  hasError: boolean,
  interactionType: string | undefined,
  isRunning: boolean
): string {
  if (hasError)   return "error";
  if (isComplete) return "complete";
  if (interactionType === "select_use_cases") return "use-cases";
  if (interactionType === "select_solution")  return "solution";
  if (isRunning)  return "idle";
  return "idle";
}

export default function ScanPage({ params }: PageProps) {
  const { sessionId } = use(params);
  const {
    nodes, isConnected, isComplete, error,
    currentNode, pendingInteraction, submitInteraction,
  } = useAgentStream(sessionId);

  const [interacting, setInteracting] = useState(false);

  const completedCount = nodes.filter((n) => n.status === "complete").length;
  const isRunning = nodes.some((n) => n.status === "running");
  const progressPct = isComplete ? 100 : nodes.length > 0
    ? Math.round((completedCount / nodes.length) * 100)
    : 0;
  const isAwaiting = !!pendingInteraction;

  async function handleUseCaseSubmit(ids: string[]) {
    setInteracting(true);
    await submitInteraction({ selected_use_case_ids: ids });
    setInteracting(false);
  }

  async function handleSolutionSubmit(id: string) {
    setInteracting(true);
    await submitInteraction({ selected_solution_id: id });
    setInteracting(false);
  }

  function statusLabel() {
    if (isComplete) return "Analysis complete.";
    if (isAwaiting && pendingInteraction?.type === "select_use_cases") return "Your input needed — select use cases";
    if (isAwaiting && pendingInteraction?.type === "select_solution")  return "Your input needed — choose a solution";
    if (currentNode) {
      const n = nodes.find((n) => n.name === currentNode);
      return `${n?.label ?? "Running"}…`;
    }
    if (isRunning) {
      const runningNode = nodes.find((n) => n.status === "running");
      return `${runningNode?.label ?? "Running"}…`;
    }
    return "Starting pipeline…";
  }

  const panelKey = rightPanelKey(isComplete, !!error, pendingInteraction?.type, isRunning || isConnected);

  return (
    <div className="min-h-screen bg-neutral-950">
      {/* Header */}
      <header className="border-b border-neutral-800">
        <Container>
          <div className="flex h-16 items-center justify-between">
            <Link href="/" className="font-display text-lg font-medium text-white hover:text-neutral-300 transition">
              DivAi
            </Link>
            <div className="flex items-center gap-2 text-xs">
              <AnimatePresence mode="wait">
                {isAwaiting && (
                  <motion.span
                    key="awaiting"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ duration: 0.15 }}
                    className="flex items-center gap-1.5 rounded-full border border-yellow-700 bg-yellow-900/20 px-3 py-1 text-yellow-400 font-medium"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-yellow-400 animate-pulse" />
                    Awaiting your input
                  </motion.span>
                )}
                {isConnected && !isAwaiting && (
                  <motion.span
                    key="live"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className="flex items-center gap-1.5 text-blue-400 font-medium"
                  >
                    <Radio className="h-3 w-3 animate-pulse" /> Live
                  </motion.span>
                )}
                {isComplete && (
                  <motion.span
                    key="complete"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-green-400 font-medium"
                  >
                    Complete
                  </motion.span>
                )}
                {error && (
                  <motion.span
                    key="error"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-red-400 font-medium"
                  >
                    Error
                  </motion.span>
                )}
              </AnimatePresence>
            </div>
          </div>
        </Container>
      </header>

      <Container className="py-12">
        {/* Title + progress */}
        <FadeIn>
          <div className="mb-10">
            <p className="text-xs font-medium uppercase tracking-widest text-neutral-500 mb-3">
              Pipeline
            </p>
            <AnimatePresence mode="wait">
              <motion.h1
                key={statusLabel()}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.25 }}
                className="font-display text-3xl font-medium text-white sm:text-4xl"
              >
                {statusLabel()}
              </motion.h1>
            </AnimatePresence>

            <div className="mt-5 h-1 w-full max-w-sm rounded-full bg-neutral-800">
              <motion.div
                className={clsx(
                  "h-full rounded-full",
                  isComplete ? "bg-green-500" : isAwaiting ? "bg-yellow-500" : "bg-blue-600"
                )}
                animate={{ width: `${progressPct}%` }}
                transition={{ duration: 0.7, ease: "easeInOut" }}
                style={{ width: `${progressPct}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-neutral-600">
              {completedCount} of {nodes.length} stages complete
            </p>
          </div>
        </FadeIn>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Node cards — left/main column */}
          <div className="lg:col-span-2 space-y-3">
            <FadeInStagger faster>
              {nodes.map((node, i) => (
                <FadeIn key={node.name}>
                  <NodeCard node={node} index={i} />
                </FadeIn>
              ))}
            </FadeInStagger>
          </div>

          {/* Right column — smoothly transitions between states */}
          <div className="lg:sticky lg:top-6">
            <AnimatePresence mode="wait">
              <motion.div
                key={panelKey}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.25, ease: "easeInOut" }}
              >
                {/* Use case selector */}
                {pendingInteraction?.type === "select_use_cases" && pendingInteraction.use_cases && (
                  <UseCaseSelector
                    useCases={pendingInteraction.use_cases}
                    onSubmit={handleUseCaseSubmit}
                    isLoading={interacting}
                  />
                )}

                {/* Solution selector */}
                {pendingInteraction?.type === "select_solution" && pendingInteraction.solutions && (
                  <SolutionSelector
                    solutions={pendingInteraction.solutions}
                    onSubmit={handleSolutionSubmit}
                    isLoading={interacting}
                  />
                )}

                {/* Idle hint while running */}
                {!pendingInteraction && !isComplete && !error && (
                  <div className="rounded-2xl border border-neutral-800 bg-neutral-950/50 p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" />
                      <span className="text-xs font-medium text-neutral-500">Running</span>
                    </div>
                    <p className="text-xs text-neutral-600 leading-relaxed">
                      The pipeline is analysing the site. You&apos;ll be asked to review use cases and choose a solution before the proposal is written.
                    </p>
                  </div>
                )}

                {/* Complete CTA */}
                {isComplete && (
                  <div className="rounded-2xl border border-neutral-700 bg-neutral-950 p-6">
                    <p className="text-xs font-medium uppercase tracking-widest text-green-400 mb-2">
                      Pipeline complete
                    </p>
                    <p className="text-sm text-neutral-400 mb-5 leading-relaxed">
                      Your proposal is ready. View the full intelligence report, use cases, solutions, and download the proposal document.
                    </p>
                    <Link
                      href={`/report/${sessionId}`}
                      className="flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-neutral-950 hover:bg-neutral-100 transition"
                    >
                      View full report
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                    <Link href="/" className="mt-3 block text-center text-xs text-neutral-500 hover:text-neutral-300 transition">
                      Scan another site
                    </Link>
                  </div>
                )}

                {/* Error CTA */}
                {error && (
                  <div className="rounded-2xl border border-red-800 bg-red-950/20 p-5">
                    <p className="text-sm font-semibold text-red-300 mb-1">Pipeline error</p>
                    <p className="text-xs text-red-400 mb-4">{error}</p>
                    <Link href="/" className="text-xs font-medium text-white hover:text-neutral-300 transition">
                      ← Try again
                    </Link>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </Container>
    </div>
  );
}

function clsx(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
