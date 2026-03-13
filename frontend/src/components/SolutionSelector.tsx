"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";
import { SolutionCard } from "@/types/divai";
import { ArrowRight } from "lucide-react";

interface SolutionSelectorProps {
  solutions: SolutionCard[];
  onSubmit: (id: string) => void;
  isLoading?: boolean;
}

const effortDot: Record<string, string> = {
  Low:    "bg-green-500",
  Medium: "bg-yellow-500",
  High:   "bg-red-500",
};

export function SolutionSelector({ solutions, onSubmit, isLoading }: SolutionSelectorProps) {
  const [selected, setSelected] = useState<string>(solutions[0]?.id ?? "");

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="rounded-2xl border border-neutral-800 bg-neutral-950 overflow-hidden"
    >
      {/* Header */}
      <div className="px-5 pt-5 pb-4">
        <p className="text-xs font-medium text-neutral-500 uppercase tracking-widest mb-1">Your input</p>
        <h3 className="text-sm font-semibold text-white">Choose a solution to build</h3>
      </div>

      {/* Divider */}
      <div className="h-px bg-neutral-800 mx-5" />

      {/* List */}
      <div className="py-2">
        {solutions.map((sol) => {
          const isSelected = selected === sol.id;
          return (
            <div key={sol.id}>
              <button
                onClick={() => setSelected(sol.id)}
                className={clsx(
                  "relative w-full px-5 py-3 text-left transition-colors duration-150 focus:outline-none group",
                  isSelected ? "bg-neutral-900" : "hover:bg-neutral-900/50"
                )}
              >
                {/* Left accent */}
                <motion.div
                  className="absolute left-0 top-1 bottom-1 w-0.5 rounded-full bg-blue-500"
                  initial={false}
                  animate={{ opacity: isSelected ? 1 : 0, scaleY: isSelected ? 1 : 0.4 }}
                  transition={{ duration: 0.18 }}
                />

                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className={clsx(
                      "text-sm font-medium leading-snug transition-colors duration-150",
                      isSelected ? "text-white" : "text-neutral-400 group-hover:text-neutral-200"
                    )}>
                      {sol.title}
                    </p>
                    <p className="text-xs text-neutral-600 mt-0.5 line-clamp-1">{sol.pitch}</p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 mt-0.5">
                    {/* Effort dot */}
                    <span className={clsx(
                      "h-1.5 w-1.5 rounded-full shrink-0",
                      effortDot[sol.effort_score] ?? "bg-neutral-600"
                    )} />
                    <span className="text-xs text-neutral-600 tabular-nums whitespace-nowrap">{sol.timeline}</span>
                    {/* Radio */}
                    <div className={clsx(
                      "h-4 w-4 rounded-full border-2 flex items-center justify-center transition-colors duration-150",
                      isSelected ? "border-blue-500" : "border-neutral-700"
                    )}>
                      <AnimatePresence initial={false}>
                        {isSelected && (
                          <motion.div
                            key="dot"
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            exit={{ scale: 0 }}
                            transition={{ duration: 0.12 }}
                            className="h-2 w-2 rounded-full bg-blue-500"
                          />
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                </div>
              </button>

              {/* Phases — expand inline under selected */}
              <AnimatePresence initial={false}>
                {isSelected && sol.phases?.length > 0 && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.22, ease: "easeInOut" }}
                    style={{ overflow: "hidden" }}
                    className="px-5 pb-3 bg-neutral-900"
                  >
                    <ul className="space-y-1 pt-1 border-l border-neutral-800 pl-3 ml-1">
                      {sol.phases.map((p, i) => (
                        <li key={i} className="text-xs text-neutral-500 leading-relaxed">{p}</li>
                      ))}
                    </ul>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>

      {/* Divider */}
      <div className="h-px bg-neutral-800 mx-5" />

      {/* Footer */}
      <div className="px-5 py-4">
        <button
          onClick={() => selected && onSubmit(selected)}
          disabled={!selected || isLoading}
          className="w-full flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-neutral-950 hover:bg-neutral-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors duration-150"
        >
          {isLoading ? (
            <span className="h-4 w-4 rounded-full border-2 border-neutral-400 border-t-neutral-900 animate-spin" />
          ) : (
            <>
              Build this solution
              <ArrowRight className="h-3.5 w-3.5" />
            </>
          )}
        </button>
      </div>
    </motion.div>
  );
}
