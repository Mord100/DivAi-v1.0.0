"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Lock, FileText, CheckCircle2, ShieldCheck, Tag, X } from "lucide-react";

interface PaywallModalProps {
  isOpen: boolean;
  onConfirm: () => void;  // wire Paychange here when ready
  onBack: () => void;
}

const INCLUDED = [
  "Full technical proposal document (.docx)",
  "Executive summary & investment breakdown",
  "Phase-by-phase delivery plan",
  "Architecture & tech stack recommendations",
  "API specifications & testing strategy",
  "Risk register & compliance notes",
];

// TODO: replace with server-side promo code validation when Paychange is integrated
const VALID_PROMO_CODES: Record<string, { discount: number; label: string }> = {
  "DIV.AI-100": { discount: 100, label: "100% off" },
};

export function PaywallModal({ isOpen, onConfirm, onBack }: PaywallModalProps) {
  const [promoInput, setPromoInput] = useState("");
  const [promoOpen, setPromoOpen] = useState(false);
  const [appliedPromo, setAppliedPromo] = useState<{ code: string; discount: number; label: string } | null>(null);
  const [promoError, setPromoError] = useState<string | null>(null);
  const [paymentError, setPaymentError] = useState<string | null>(null);

  const effectivePrice = appliedPromo?.discount === 100 ? 0 : 0.99;

  function handleApplyPromo() {
    const code = promoInput.trim().toUpperCase();
    const match = VALID_PROMO_CODES[code];
    if (match) {
      setAppliedPromo({ code, ...match });
      setPromoError(null);
      setPromoOpen(false);
      setPromoInput("");
    } else {
      setPromoError("Invalid promo code.");
    }
  }

  function handleRemovePromo() {
    setAppliedPromo(null);
    setPromoError(null);
  }

  function handleConfirm() {
    if (effectivePrice === 0) {
      // Valid 100% promo — skip payment entirely
      onConfirm();
    } else {
      // TODO: open Paychange checkout session, call onConfirm() on success
      setPaymentError("Payment gateway not yet configured. Enter a promo code to unlock.");
    }
  }

  function handleClose() {
    setPromoInput("");
    setPromoOpen(false);
    setAppliedPromo(null);
    setPromoError(null);
    setPaymentError(null);
    onBack();
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop — not clickable, user must use Back button */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-neutral-950/80 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            key="modal"
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.97 }}
            transition={{ duration: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="w-full max-w-md rounded-2xl border border-neutral-800 bg-neutral-950 overflow-hidden shadow-2xl">

              {/* Header */}
              <div className="px-6 pt-6 pb-5 border-b border-neutral-800">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-9 w-9 rounded-full bg-blue-600/10 border border-blue-600/20 flex items-center justify-center">
                    <Lock className="h-4 w-4 text-blue-400" />
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase tracking-widest text-neutral-500">Unlock</p>
                    <h2 className="font-display text-lg font-semibold text-white leading-tight">
                      Generate your proposal
                    </h2>
                  </div>
                </div>
                <p className="text-sm text-neutral-400 leading-relaxed">
                  Your analysis is complete. Unlock the full technical proposal — a ready-to-send document your team can act on immediately.
                </p>
              </div>

              {/* What's included */}
              <div className="px-6 py-5 border-b border-neutral-800">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="h-3.5 w-3.5 text-neutral-500" />
                  <p className="text-xs font-medium uppercase tracking-widest text-neutral-500">What&apos;s included</p>
                </div>
                <ul className="space-y-2">
                  {INCLUDED.map((item) => (
                    <li key={item} className="flex items-start gap-2.5">
                      <CheckCircle2 className="h-4 w-4 text-blue-500 shrink-0 mt-0.5" />
                      <span className="text-sm text-neutral-300">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* CTA */}
              <div className="px-6 py-5">

                {/* Price */}
                <div className="flex items-baseline gap-2 mb-4">
                  {appliedPromo ? (
                    <>
                      <span className="font-display text-3xl font-semibold text-white">
                        {effectivePrice === 0 ? "Free" : `$${effectivePrice}`}
                      </span>
                      <span className="text-sm line-through text-neutral-600">$0.99</span>
                      <span className="text-xs font-medium text-green-400 bg-green-400/10 rounded-full px-2 py-0.5">
                        {appliedPromo.label}
                      </span>
                    </>
                  ) : (
                    <>
                      {/* TODO: replace with live price from Paychange product config */}
                      <span className="font-display text-3xl font-semibold text-white">$0.99</span>
                      <span className="text-sm text-neutral-500">per report</span>
                    </>
                  )}
                </div>

                {/* Applied promo tag */}
                {appliedPromo && (
                  <div className="flex items-center justify-between rounded-xl border border-green-800/50 bg-green-900/10 px-3 py-2 mb-3">
                    <div className="flex items-center gap-2">
                      <Tag className="h-3.5 w-3.5 text-green-400" />
                      <span className="text-xs font-medium text-green-400">{appliedPromo.code}</span>
                    </div>
                    <button onClick={handleRemovePromo} className="text-neutral-600 hover:text-neutral-400 transition">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}

                {/* Promo code input */}
                {!appliedPromo && (
                  <div className="mb-3">
                    {!promoOpen ? (
                      <button
                        onClick={() => { setPromoOpen(true); setPaymentError(null); }}
                        className="flex items-center gap-1.5 text-xs text-neutral-500 hover:text-neutral-300 transition"
                      >
                        <Tag className="h-3.5 w-3.5" />
                        Have a promo code?
                      </button>
                    ) : (
                      <AnimatePresence>
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          className="flex gap-2"
                        >
                          <input
                            type="text"
                            value={promoInput}
                            onChange={(e) => { setPromoInput(e.target.value); setPromoError(null); }}
                            onKeyDown={(e) => e.key === "Enter" && handleApplyPromo()}
                            placeholder="Enter code"
                            className="flex-1 rounded-xl border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-white placeholder-neutral-600 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500/30 transition uppercase"
                          />
                          <button
                            onClick={handleApplyPromo}
                            className="rounded-xl bg-neutral-800 px-3 py-2 text-xs font-medium text-white hover:bg-neutral-700 transition"
                          >
                            Apply
                          </button>
                        </motion.div>
                      </AnimatePresence>
                    )}
                    {promoError && (
                      <p className="mt-1.5 text-xs text-red-400">{promoError}</p>
                    )}
                  </div>
                )}

                {/* TODO: wire to Paychange checkout when effectivePrice > 0 */}
                <button
                  onClick={handleConfirm}
                  className="w-full flex items-center justify-center gap-2 rounded-full bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-500 transition-colors duration-150"
                >
                  <Lock className="h-4 w-4" />
                  {effectivePrice === 0 ? "Unlock for free" : "Unlock report"}
                </button>

                {paymentError && (
                  <p className="mt-2 text-xs text-center text-amber-400">{paymentError}</p>
                )}

                <button
                  onClick={handleClose}
                  className="mt-3 w-full text-center text-xs text-neutral-600 hover:text-neutral-400 transition-colors duration-150"
                >
                  ← Back to solution selection
                </button>

                {effectivePrice > 0 && (
                  <div className="mt-4 flex items-center justify-center gap-1.5 text-xs text-neutral-700">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    <span>Secure payment</span>
                  </div>
                )}
              </div>

            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
