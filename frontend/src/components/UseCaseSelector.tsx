"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";
import { UseCase } from "@/types/divai";
import { ArrowRight } from "lucide-react";

interface UseCaseSelectorProps {
  useCases: UseCase[];
  onSubmit: (ids: string[]) => void;
  isLoading?: boolean;
}

export function UseCaseSelector({ useCases, onSubmit, isLoading }: UseCaseSelectorProps) {
  const [selected, setSelected] = useState<Set<string>>(
    new Set(useCases.slice(0, 2).map((u) => u.id))
  );

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

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
        <h3 className="text-sm font-semibold text-white">Select use cases to pursue</h3>
      </div>

      {/* Divider */}
      <div className="h-px bg-neutral-800 mx-5" />

      {/* List */}
      <div className="py-2">
        {useCases.map((uc, i) => {
          const isSelected = selected.has(uc.id);
          const pct = Math.round((uc.confidence_score ?? 0) * 100);
          return (
            <button
              key={uc.id}
              onClick={() => toggle(uc.id)}
              className={clsx(
                "relative w-full px-5 py-3 text-left transition-colors duration-150 focus:outline-none group",
                isSelected ? "bg-neutral-900" : "hover:bg-neutral-900/50"
              )}
            >
              {/* Left accent line */}
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
                    {uc.title}
                  </p>
                  {uc.description && (
                    <p className="text-xs text-neutral-600 mt-0.5 leading-relaxed line-clamp-2">
                      {uc.description}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0 mt-0.5">
                  <span className={clsx(
                    "text-xs tabular-nums font-medium transition-colors duration-150",
                    isSelected ? "text-blue-400" : "text-neutral-600"
                  )}>
                    {pct}%
                  </span>
                  {/* Checkbox */}
                  <div className={clsx(
                    "h-4 w-4 rounded border flex items-center justify-center transition-colors duration-150",
                    isSelected ? "border-blue-500 bg-blue-500" : "border-neutral-700"
                  )}>
                    <AnimatePresence initial={false}>
                      {isSelected && (
                        <motion.svg
                          key="check"
                          initial={{ opacity: 0, scale: 0.5 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.5 }}
                          transition={{ duration: 0.12 }}
                          className="h-2.5 w-2.5 text-white"
                          fill="none"
                          viewBox="0 0 10 8"
                        >
                          <path d="M1 4l3 3 5-6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </motion.svg>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Divider */}
      <div className="h-px bg-neutral-800 mx-5" />

      {/* Footer */}
      <div className="px-5 py-4">
        <button
          onClick={() => onSubmit(Array.from(selected))}
          disabled={selected.size === 0 || isLoading}
          className="w-full flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-neutral-950 hover:bg-neutral-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors duration-150"
        >
          {isLoading ? (
            <span className="h-4 w-4 rounded-full border-2 border-neutral-400 border-t-neutral-900 animate-spin" />
          ) : (
            <>
              Continue with {selected.size} selected
              <ArrowRight className="h-3.5 w-3.5" />
            </>
          )}
        </button>
      </div>
    </motion.div>
  );
}
