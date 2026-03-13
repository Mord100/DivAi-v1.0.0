"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";
import { NodeState } from "@/types/divai";
import { Check, Loader2, Lock, AlertCircle, ChevronDown, ChevronUp } from "lucide-react";

interface NodeCardProps { node: NodeState; index: number }

function StatusIcon({ status }: { status: NodeState["status"] }) {
  if (status === "complete") return <Check className="h-4 w-4 text-white" />;
  if (status === "running")  return <Loader2 className="h-4 w-4 text-white animate-spin" />;
  if (status === "error")    return <AlertCircle className="h-4 w-4 text-white" />;
  return <Lock className="h-4 w-4 text-neutral-500" />;
}

function FullDetail({ node }: { node: NodeState }) {
  const d = node.data;
  if (!d) return null;

  if (node.name === "ingestion" && d.scrape_summary) {
    const s = d.scrape_summary;
    return (
      <div className="mt-4 space-y-3 border-t border-neutral-800 pt-4">
        <Row label="URL" value={s.url} />
        <Row label="DOM size" value={`${s.dom_chars.toLocaleString()} chars`} />
        <Row label="Network requests" value={String(s.request_count)} />
        {s.tech_detected?.length > 0 && (
          <Row label="Tech detected" value={s.tech_detected.join(", ")} />
        )}
      </div>
    );
  }

  if (node.name === "analysis" && d.report_summary) {
    const r = d.report_summary;
    return (
      <div className="mt-4 space-y-3 border-t border-neutral-800 pt-4">
        <Row label="Category" value={r.business_category} />
        <Row label="Features" value={`${r.key_features_count} detected`} />
        <Row label="API endpoints" value={`${r.endpoints_count} found`} />
        {r.key_features?.length > 0 && (
          <div className="pt-2">
            <p className="text-xs text-neutral-500 mb-2">Key features</p>
            <div className="flex flex-wrap gap-1.5">
              {r.key_features.map((f: string) => (
                <span key={f} className="rounded-full bg-neutral-800 px-2.5 py-0.5 text-xs text-neutral-300">{f}</span>
              ))}
            </div>
          </div>
        )}
        {r.integrations?.length > 0 && (
          <div className="pt-1">
            <p className="text-xs text-neutral-500 mb-2">Integrations</p>
            <div className="flex flex-wrap gap-1.5">
              {r.integrations.map((i: string) => (
                <span key={i} className="rounded-full bg-blue-900/40 px-2.5 py-0.5 text-xs text-blue-300">{i}</span>
              ))}
            </div>
          </div>
        )}
        {r.analyst_notes && (
          <div className="pt-2">
            <p className="text-xs text-neutral-500 mb-1">Analyst notes</p>
            <p className="text-xs text-neutral-400 leading-relaxed">{r.analyst_notes}</p>
          </div>
        )}
      </div>
    );
  }

  if (node.name === "use_case" && d.use_case_titles) {
    return (
      <div className="mt-4 space-y-2 border-t border-neutral-800 pt-4">
        {d.use_case_titles.map((uc: { title: string; confidence: number }, i: number) => (
          <div key={i} className="flex items-center justify-between gap-3">
            <span className="text-sm text-neutral-300">{uc.title}</span>
            <div className="flex items-center gap-2 shrink-0">
              <div className="w-16 h-1 rounded-full bg-neutral-800">
                <div className="h-full rounded-full bg-blue-500" style={{ width: `${Math.round((uc.confidence ?? 0) * 100)}%` }} />
              </div>
              <span className="text-xs text-blue-400 w-8 text-right">{Math.round((uc.confidence ?? 0) * 100)}%</span>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (node.name === "solution" && d.solution_titles) {
    return (
      <div className="mt-4 space-y-2 border-t border-neutral-800 pt-4">
        {d.solution_titles.map((s: { title: string; timeline: string }, i: number) => (
          <div key={i} className="flex items-center justify-between gap-3">
            <span className="text-sm text-neutral-300">{s.title}</span>
            <span className="text-xs text-neutral-500 shrink-0">{s.timeline}</span>
          </div>
        ))}
      </div>
    );
  }

  if (node.name === "proposal" && d.proposal) {
    return (
      <div className="mt-4 border-t border-neutral-800 pt-4">
        <p className="text-sm font-medium text-white">{d.proposal.title}</p>
        <p className="mt-0.5 text-xs text-neutral-400">For {d.proposal.client}</p>
      </div>
    );
  }

  return null;
}

function Row({ label, value }: { label: string; value?: string }) {
  return (
    <div className="flex items-start justify-between gap-4 text-sm">
      <span className="text-neutral-500 shrink-0">{label}</span>
      <span className="text-neutral-300 text-right">{value ?? "—"}</span>
    </div>
  );
}

function CompactPreview({ node }: { node: NodeState }) {
  const d = node.data;
  if (!d) return null;
  if (node.name === "ingestion" && d.scrape_summary)
    return <p className="text-sm text-neutral-400 mt-1 truncate">{d.scrape_summary.url} · {d.scrape_summary.request_count} requests</p>;
  if (node.name === "analysis" && d.report_summary)
    return <p className="text-sm text-neutral-400 mt-1 truncate">{d.report_summary.business_category} · {d.report_summary.endpoints_count} endpoints</p>;
  if (node.name === "use_case" && d.use_case_titles?.[0])
    return <p className="text-sm text-neutral-400 mt-1 truncate">Top: {d.use_case_titles[0].title}</p>;
  if (node.name === "solution" && d.solution_titles?.[0])
    return <p className="text-sm text-neutral-400 mt-1 truncate">{d.solution_titles[0].title}</p>;
  if (node.name === "proposal" && d.proposal)
    return <p className="text-sm text-neutral-400 mt-1 truncate">{d.proposal.title}</p>;
  return null;
}

export function NodeCard({ node, index }: NodeCardProps) {
  const [expanded, setExpanded] = useState(false);
  const isComplete = node.status === "complete";
  const isRunning  = node.status === "running";
  const isError    = node.status === "error";
  const isPending  = node.status === "pending";
  const hasDetail  = isComplete && node.data;

  return (
    <div className={clsx(
      "rounded-2xl border transition-all duration-500",
      isComplete && "bg-neutral-950 border-neutral-800",
      isRunning  && "bg-neutral-950 border-blue-600",
      isError    && "bg-neutral-950 border-red-800",
      isPending  && "bg-neutral-950/40 border-neutral-800/50"
    )}>
      <div className="p-5">
        <div className="flex items-start gap-4">
          {/* Status badge */}
          <div className="shrink-0 mt-0.5">
            <div className={clsx(
              "flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold",
              isComplete && "bg-blue-600",
              isRunning  && "bg-blue-600",
              isError    && "bg-red-700",
              isPending  && "bg-neutral-800 text-neutral-500"
            )}>
              {isPending ? index + 1 : <StatusIcon status={node.status} />}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <p className={clsx("text-sm font-semibold", isPending ? "text-neutral-500" : "text-white")}>
                {node.label}
              </p>
              <div className="flex items-center gap-2 shrink-0">
                {isRunning && (
                  <span className="text-xs text-blue-400 animate-pulse">Running</span>
                )}
                {isComplete && <span className="text-xs text-neutral-600">Done</span>}
                {hasDetail && (
                  <button
                    onClick={() => setExpanded(!expanded)}
                    className="flex items-center gap-1 text-xs text-neutral-500 hover:text-neutral-300 transition-colors ml-1"
                  >
                    {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                    {expanded ? "Less" : "Details"}
                  </button>
                )}
              </div>
            </div>

            {/* Running indicator — subtle pulse */}
            {isRunning && (
              <div className="mt-2 h-px w-full rounded-full bg-blue-600/40 animate-pulse" />
            )}

            {isError && (
              <p className="mt-2 text-xs text-red-400">{node.data?.error ?? "An error occurred"}</p>
            )}

            {/* Animated expand/collapse — smooth height transition */}
            <AnimatePresence mode="wait" initial={false}>
              {isComplete && !expanded && hasDetail && (
                <motion.div
                  key="preview"
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.18, ease: "easeOut" }}
                >
                  <CompactPreview node={node} />
                </motion.div>
              )}
              {isComplete && expanded && (
                <motion.div
                  key="full"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.28, ease: [0.25, 0.46, 0.45, 0.94] }}
                  style={{ overflow: "hidden" }}
                >
                  <FullDetail node={node} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
