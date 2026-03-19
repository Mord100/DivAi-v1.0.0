"use client";

import { useState, useEffect, FormEvent, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import clsx from "clsx";
import { Container } from "@/components/Container";
import { ArrowRight, ArrowLeft, Check, Loader2, Copy, KeyRound, Eye, EyeOff } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Types ────────────────────────────────────────────────────────────────────

interface FormField {
  tag: string;
  type: string;
  id: string | null;
  name: string | null;
  placeholder: string | null;
  label: string | null;
  required: boolean;
  autocomplete: string | null;
  options: Array<{ value: string; text: string }> | null;
}

interface InspectResult {
  signup_url: string;
  fields: FormField[];
  submit_selector: string;
  found_signup_link: boolean;
  error: string | null;
}

interface CaptureResult {
  auth_cookie: { name: string; value: string; domain: string } | null;
  all_cookies: Array<{ name: string; value: string }>;
  final_url: string;
}

type Step = "url" | "inspect" | "fill" | "capture" | "done";

// ── Field key: prefer id, fall back to name ──────────────────────────────────
function fieldKey(f: FormField): string {
  return f.id || f.name || "";
}

function fieldLabel(f: FormField): string {
  return f.label || f.placeholder || f.id || f.name || f.type;
}

// ── Individual form field renderer ───────────────────────────────────────────
function FieldInput({
  field,
  value,
  onChange,
}: {
  field: FormField;
  value: string;
  onChange: (v: string) => void;
}) {
  const [showPassword, setShowPassword] = useState(false);
  const key = fieldKey(field);
  const label = fieldLabel(field);
  const isPassword = field.type === "password";
  const inputType = isPassword ? (showPassword ? "text" : "password") : field.type;

  if (field.tag === "select" && field.options?.length) {
    return (
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-neutral-400">
          {label}
          {field.required && <span className="text-red-400 ml-1">*</span>}
        </label>
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={field.required}
          className="w-full rounded-xl border border-neutral-700 bg-neutral-900 px-4 py-2.5 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500/30 transition"
        >
          <option value="">Select…</option>
          {field.options.map((o) => (
            <option key={o.value} value={o.value}>{o.text}</option>
          ))}
        </select>
      </div>
    );
  }

  if (field.type === "checkbox") {
    return (
      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="checkbox"
          checked={value === "true"}
          onChange={(e) => onChange(e.target.checked ? "true" : "false")}
          className="h-4 w-4 rounded border-neutral-600 bg-neutral-900 text-blue-600 focus:ring-blue-500/30"
        />
        <span className="text-sm text-neutral-300">{label}</span>
      </label>
    );
  }

  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-neutral-400">
        {label}
        {field.required && <span className="text-red-400 ml-1">*</span>}
      </label>
      <div className="relative">
        <input
          type={inputType}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder ?? ""}
          required={field.required}
          autoComplete={field.autocomplete ?? undefined}
          className="w-full rounded-xl border border-neutral-700 bg-neutral-900 px-4 py-2.5 text-sm text-white placeholder-neutral-600 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500/30 transition pr-10"
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300 transition"
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}
      </div>
    </div>
  );
}

// ── Step indicator ────────────────────────────────────────────────────────────
function StepIndicator({ current }: { current: number }) {
  const steps = ["Enter URL", "Inspect form", "Sign up", "Done"];
  return (
    <div className="flex items-center gap-0 mb-10">
      {steps.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={label} className="flex items-center">
            <div className="flex flex-col items-center gap-1.5">
              <div className={clsx(
                "h-7 w-7 rounded-full flex items-center justify-center text-xs font-semibold transition-colors duration-300",
                done   ? "bg-blue-600 text-white" :
                active ? "bg-blue-600 text-white" :
                         "bg-neutral-800 text-neutral-500"
              )}>
                {done ? <Check className="h-3.5 w-3.5" /> : i + 1}
              </div>
              <span className={clsx(
                "text-xs whitespace-nowrap transition-colors duration-300",
                active ? "text-white" : done ? "text-blue-400" : "text-neutral-600"
              )}>
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={clsx(
                "h-px w-12 sm:w-20 mx-2 mb-5 transition-colors duration-300",
                done ? "bg-blue-600" : "bg-neutral-800"
              )} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
function AuthCaptureContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [step, setStep] = useState<Step>("url");
  const [url, setUrl] = useState(searchParams.get("url") ?? "");
  const [inspectResult, setInspectResult] = useState<InspectResult | null>(null);
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [captureResult, setCaptureResult] = useState<CaptureResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const stepIndex: Record<Step, number> = {
    url: 0, inspect: 1, fill: 1, capture: 2, done: 3,
  };

  // Auto-inspect if URL was passed as query param
  useEffect(() => {
    const preloadUrl = searchParams.get("url");
    if (preloadUrl) {
      setUrl(preloadUrl);
      handleInspect(preloadUrl);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleInspect(targetUrl?: string) {
    const u = (targetUrl ?? url).trim();
    if (!u) return;
    setError(null);
    setStep("inspect");

    try {
      const res = await fetch(`${API_URL}/api/auth/inspect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: u }),
      });
      const data: InspectResult = await res.json();
      if (!res.ok) throw new Error((data as unknown as { detail: string }).detail ?? "Inspection failed");

      setInspectResult(data);
      // Pre-fill autocomplete hints
      const initial: Record<string, string> = {};
      data.fields.forEach((f) => {
        initial[fieldKey(f)] = "";
      });
      setFieldValues(initial);
      setStep("fill");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Inspection failed");
      setStep("url");
    }
  }

  async function handleCapture(e: FormEvent) {
    e.preventDefault();
    if (!inspectResult) return;
    setError(null);
    setStep("capture");

    try {
      const res = await fetch(`${API_URL}/api/auth/capture`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          signup_url: inspectResult.signup_url,
          field_values: fieldValues,
          submit_selector: inspectResult.submit_selector,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Capture failed");

      setCaptureResult(data);
      setStep("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Capture failed");
      setStep("fill");
    }
  }

  async function handleScan() {
    if (!url || !captureResult) return;
    try {
      const res = await fetch(`${API_URL}/api/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: url.trim(),
          depth: "surface",
          cookies: captureResult.all_cookies,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Scan failed");
      router.push(`/scan/${data.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    }
  }

  function copyCookie() {
    if (!captureResult?.auth_cookie) return;
    const val = `${captureResult.auth_cookie.name}=${captureResult.auth_cookie.value}`;
    navigator.clipboard.writeText(val);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  // Visible/useful fields only (skip hidden, submit buttons already filtered backend-side)
  const fillableFields = inspectResult?.fields.filter(
    (f) => !["hidden", "submit", "button", "image", "reset"].includes(f.type)
  ) ?? [];

  return (
    <div className="min-h-screen bg-neutral-950">
      {/* Header */}
      <header className="border-b border-neutral-800">
        <Container>
          <div className="flex h-16 items-center gap-4">
            <Link href="/" className="flex items-center gap-1.5 text-sm font-medium text-neutral-400 hover:text-white transition">
              <ArrowLeft className="h-4 w-4" /> Home
            </Link>
            <div className="h-4 w-px bg-neutral-800" />
            <span className="font-display text-lg font-medium text-white">Auth Capture</span>
          </div>
        </Container>
      </header>

      <Container className="py-12 max-w-2xl">
        <StepIndicator current={stepIndex[step]} />

        <AnimatePresence mode="wait">

          {/* ── Step 0: URL entry ── */}
          {(step === "url") && (
            <motion.div
              key="url"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.22 }}
            >
              <p className="text-xs font-medium uppercase tracking-widest text-neutral-500 mb-2">Step 1</p>
              <h1 className="font-display text-3xl font-medium text-white mb-2">Enter the site URL</h1>
              <p className="text-sm text-neutral-500 mb-8 leading-relaxed">
                We&apos;ll find the signup page, extract all form fields, and let you fill in your own credentials.
              </p>

              <form onSubmit={(e) => { e.preventDefault(); handleInspect(); }} className="space-y-4">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://linear.app"
                  required
                  className="w-full rounded-xl border border-neutral-700 bg-neutral-900 px-5 py-3 text-white placeholder-neutral-600 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500/30 transition text-sm"
                />
                {error && <p className="text-sm text-red-400">{error}</p>}
                <button
                  type="submit"
                  className="flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-neutral-950 hover:bg-neutral-100 transition"
                >
                  Inspect signup form
                  <ArrowRight className="h-4 w-4" />
                </button>
              </form>
            </motion.div>
          )}

          {/* ── Inspecting… ── */}
          {step === "inspect" && (
            <motion.div
              key="inspecting"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.22 }}
              className="flex flex-col items-center py-16 gap-4"
            >
              <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
              <p className="text-sm text-neutral-400">Finding signup page and extracting form fields…</p>
              <p className="text-xs text-neutral-600">{url}</p>
            </motion.div>
          )}

          {/* ── Step 1: Fill form ── */}
          {step === "fill" && inspectResult && (
            <motion.div
              key="fill"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.22 }}
            >
              <div className="flex items-start justify-between mb-6">
                <div>
                  <p className="text-xs font-medium uppercase tracking-widest text-neutral-500 mb-2">Step 2</p>
                  <h1 className="font-display text-3xl font-medium text-white">Fill in your details</h1>
                  <p className="text-sm text-neutral-500 mt-1">
                    {fillableFields.length} fields found on{" "}
                    <span className="text-neutral-400 truncate inline-block max-w-xs align-bottom">
                      {inspectResult.signup_url}
                    </span>
                  </p>
                </div>
                <button
                  onClick={() => setStep("url")}
                  className="text-xs text-neutral-500 hover:text-neutral-300 transition mt-1"
                >
                  ← Back
                </button>
              </div>

              {error && (
                <div className="mb-4 rounded-xl border border-red-800 bg-red-950/30 px-4 py-3 text-sm text-red-400">
                  {error}
                </div>
              )}

              <form onSubmit={handleCapture} className="space-y-4">
                <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5 space-y-4">
                  {fillableFields.map((field) => (
                    <FieldInput
                      key={fieldKey(field)}
                      field={field}
                      value={fieldValues[fieldKey(field)] ?? ""}
                      onChange={(v) =>
                        setFieldValues((prev) => ({ ...prev, [fieldKey(field)]: v }))
                      }
                    />
                  ))}
                </div>

                <p className="text-xs text-neutral-600 leading-relaxed">
                  Your credentials are sent directly to {new URL(url).hostname} — they are never stored by DivAi.
                </p>

                <button
                  type="submit"
                  className="flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-neutral-950 hover:bg-neutral-100 transition"
                >
                  Sign up & capture cookie
                  <KeyRound className="h-4 w-4" />
                </button>
              </form>
            </motion.div>
          )}

          {/* ── Capturing… ── */}
          {step === "capture" && (
            <motion.div
              key="capturing"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.22 }}
              className="flex flex-col items-center py-16 gap-4"
            >
              <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
              <p className="text-sm text-neutral-400">Submitting form and capturing session cookie…</p>
            </motion.div>
          )}

          {/* ── Step 2: Done ── */}
          {step === "done" && captureResult && (
            <motion.div
              key="done"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.22 }}
            >
              <p className="text-xs font-medium uppercase tracking-widest text-neutral-500 mb-2">Step 3</p>
              <h1 className="font-display text-3xl font-medium text-white mb-1">Cookie captured</h1>
              <p className="text-sm text-neutral-500 mb-8">
                Account created and session captured. Ready for authenticated scanning.
              </p>

              {/* Auth cookie display */}
              {captureResult.auth_cookie ? (
                <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5 mb-6">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs font-medium uppercase tracking-widest text-neutral-500">Session cookie</p>
                    <button
                      onClick={copyCookie}
                      className="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-white transition"
                    >
                      {copied ? <Check className="h-3.5 w-3.5 text-green-400" /> : <Copy className="h-3.5 w-3.5" />}
                      {copied ? "Copied" : "Copy"}
                    </button>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-4 text-sm">
                      <span className="text-neutral-500 shrink-0">Name</span>
                      <span className="text-white font-mono text-xs">{captureResult.auth_cookie.name}</span>
                    </div>
                    <div className="flex items-start justify-between gap-4 text-sm">
                      <span className="text-neutral-500 shrink-0">Value</span>
                      <span className="text-neutral-400 font-mono text-xs truncate max-w-[280px]">
                        {captureResult.auth_cookie.value.slice(0, 48)}…
                      </span>
                    </div>
                    <div className="flex items-start justify-between gap-4 text-sm">
                      <span className="text-neutral-500 shrink-0">Domain</span>
                      <span className="text-neutral-400 text-xs">{captureResult.auth_cookie.domain}</span>
                    </div>
                    <div className="flex items-start justify-between gap-4 text-sm">
                      <span className="text-neutral-500 shrink-0">Landed at</span>
                      <span className="text-neutral-400 text-xs truncate max-w-[280px]">{captureResult.final_url}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-yellow-800 bg-yellow-950/20 p-4 mb-6">
                  <p className="text-sm text-yellow-400">No clear auth cookie detected — all {captureResult.all_cookies.length} cookies captured.</p>
                </div>
              )}

              {error && <p className="text-sm text-red-400 mb-4">{error}</p>}

              <div className="flex gap-3">
                <button
                  onClick={handleScan}
                  className="flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-500 transition"
                >
                  Scan with authentication
                  <ArrowRight className="h-4 w-4" />
                </button>
                <button
                  onClick={() => { setStep("url"); setInspectResult(null); setCaptureResult(null); }}
                  className="rounded-xl border border-neutral-700 px-6 py-3 text-sm font-medium text-neutral-400 hover:text-white hover:border-neutral-500 transition"
                >
                  Start over
                </button>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </Container>
    </div>
  );
}

export default function AuthCapturePage() {
  return (
    <Suspense>
      <AuthCaptureContent />
    </Suspense>
  );
}
