"use client";

/**
 * Home page — URL input form with brand-aligned hero layout.
 *
 * CONCEPT: "use client" in Next.js 14
 * -------------------------------------
 * This file needs client-side interactivity (form state, router.push).
 * Without "use client", it would be a Server Component — no hooks, no events.
 * Adding "use client" at the top makes it a Client Component that runs in
 * the browser with full React capabilities.
 */

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Container } from "@/components/Container";
import { FadeIn, FadeInStagger } from "@/components/FadeIn";
import { ArrowRight, Zap, Search, FileText, KeyRound } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const steps = [
  {
    icon: Search,
    title: "Scrape",
    description: "Playwright captures the full DOM, network traffic, JS globals, and tech fingerprints.",
  },
  {
    icon: Zap,
    title: "Analyse",
    description: "Claude reads the signals — tech stack, API patterns, business model, key features.",
  },
  {
    icon: FileText,
    title: "Propose",
    description: "A full technical proposal lands in your downloads. Tailored to this client. In minutes.",
  },
];

export default function HomePage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);

    try {
      /**
       * CONCEPT: fetch() — The Browser's HTTP Client
       * POST to our FastAPI backend with the URL to scan.
       * Returns the session_id we use to track this pipeline run.
       */
      const res = await fetch(`${API_URL}/api/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), depth: "surface" }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? "Failed to start scan");
      }

      const data = await res.json();

      // Navigate to the live pipeline progress page
      router.push(`/scan/${data.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header className="bg-neutral-950">
        <Container>
          <div className="flex h-16 items-center justify-between">
            <span className="font-display text-lg font-medium tracking-tight text-white">
              DivAi
            </span>
            <span className="text-xs font-medium tracking-widest uppercase text-neutral-500">
              AI Lead Intelligence
            </span>
          </div>
        </Container>
      </header>

      {/* ── Hero ────────────────────────────────────────────────────────────── */}
      <section className="bg-neutral-950 pb-32 pt-24">
        <Container>
          <FadeIn>
            <h1 className="font-display text-5xl font-medium tracking-tight text-white sm:text-6xl lg:text-7xl">
              Turn any website into
              <br />
              <span className="text-blue-500">a qualified lead.</span>
            </h1>
          </FadeIn>

          <FadeIn>
            <p className="mt-6 max-w-2xl text-lg text-neutral-400 leading-relaxed">
              DivAi scrapes, analyses, and writes a full technical proposal for any
              website — in under 5 minutes. Paste a URL. Get a proposal.
            </p>
          </FadeIn>

          {/* ── Scan form ─────────────────────────────────────────────────── */}
          <FadeIn>
            <form onSubmit={handleSubmit} className="mt-12">
              <div className="flex flex-col gap-3 sm:flex-row sm:max-w-2xl">
                <div className="relative flex-1">
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://stripe.com"
                    required
                    className="
                      w-full rounded-2xl border border-neutral-700 bg-neutral-900
                      px-6 py-4 text-white placeholder-neutral-600
                      focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20
                      transition
                    "
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="
                    inline-flex items-center gap-2 rounded-2xl
                    bg-blue-600 px-8 py-4 text-sm font-semibold text-white
                    hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed
                    transition shrink-0
                  "
                >
                  {loading ? (
                    <>
                      <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                      Starting…
                    </>
                  ) : (
                    <>
                      Analyse
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </div>

              {error && (
                <p className="mt-3 text-sm text-red-400">{error}</p>
              )}

              <p className="mt-4 text-sm text-neutral-600">
                Site behind a login?{" "}
                <Link
                  href={url ? `/auth-capture?url=${encodeURIComponent(url)}` : "/auth-capture"}
                  className="inline-flex items-center gap-1 text-neutral-400 hover:text-white transition"
                >
                  <KeyRound className="h-3.5 w-3.5" />
                  Sign up &amp; capture session first
                </Link>
              </p>
            </form>
          </FadeIn>
        </Container>
      </section>

      {/* ── How it works ────────────────────────────────────────────────────── */}
      <section className="border-t border-neutral-100 py-24">
        <Container>
          <FadeIn>
            <p className="text-xs font-medium uppercase tracking-widest text-neutral-400 mb-12">
              How it works
            </p>
          </FadeIn>

          <FadeInStagger faster>
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
              {steps.map((step, i) => (
                <FadeIn key={step.title}>
                  <div className="flex flex-col gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-neutral-950">
                      <step.icon className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-medium uppercase tracking-widest text-neutral-400 mb-1">
                        0{i + 1}
                      </p>
                      <h3 className="text-lg font-semibold text-neutral-950">
                        {step.title}
                      </h3>
                      <p className="mt-2 text-sm text-neutral-500 leading-relaxed">
                        {step.description}
                      </p>
                    </div>
                  </div>
                </FadeIn>
              ))}
            </div>
          </FadeInStagger>
        </Container>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <footer className="border-t border-neutral-100 py-10">
        <Container>
          <div className="flex items-center justify-between">
            <span className="text-xs text-neutral-400">
              © {new Date().getFullYear()} DivAi. AI-powered business intelligence.
            </span>
            <span className="text-xs font-medium tracking-widest uppercase text-neutral-300">
              DiV Dynamics
            </span>
          </div>
        </Container>
      </footer>
    </div>
  );
}
