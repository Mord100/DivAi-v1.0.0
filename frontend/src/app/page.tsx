"use client";

import { useState, FormEvent, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Container } from "@/components/Container";
import { FadeIn } from "@/components/FadeIn";
import { WorkflowAnimation } from "@/components/WorkflowAnimation";
import { ArrowRight, KeyRound, User, Building2, History } from "lucide-react";
import { useAuth } from "@/lib/supabase/AuthProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Step = "url" | "identity";

export default function HomePage() {
  const router  = useRouter();
  const formRef = useRef<HTMLDivElement>(null);
  const { user: authedUser } = useAuth();

  const [step, setStep]       = useState<Step>("url");
  const [url, setUrl]         = useState("");
  const [email, setEmail]     = useState("");
  const [name, setName]       = useState("");
  const [company, setCompany] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  function handleScrollToForm() {
    formRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  // Step 1: validate URL — skip identity step if already signed in
  async function handleUrlSubmit(e: FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setError(null);

    if (authedUser) {
      await startScan(
        authedUser.email ?? "",
        authedUser.user_metadata?.full_name ?? "",
        "",
        authedUser.id,   // pass Supabase auth UUID so scan links to the right user
      );
    } else {
      setStep("identity");
    }
  }

  async function startScan(emailVal: string, nameVal: string, companyVal: string, authUserId?: string) {
    setLoading(true);
    setError(null);
    try {
      let userId: string | null = null;
      const idRes = await fetch(`${API_URL}/api/users/identify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: emailVal.trim(),
          name: nameVal.trim() || null,
          company: companyVal.trim() || null,
          user_id: authUserId ?? null,
        }),
      });
      if (idRes.ok) {
        const idData = await idRes.json();
        userId = idData.user_id;
      }

      const scanRes = await fetch(`${API_URL}/api/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), depth: "surface", user_id: userId }),
      });

      if (!scanRes.ok) {
        const err = await scanRes.json();
        throw new Error(err.detail ?? "Failed to start scan");
      }

      const data = await scanRes.json();

      if (userId) {
        localStorage.setItem("divai_user_id", userId);
        localStorage.setItem("divai_user_email", emailVal.trim());
      }

      router.push(`/scan/${data.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setLoading(false);
    }
  }

  // Step 2: identity form submit
  async function handleIdentitySubmit(e: FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    await startScan(email, name, company);
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-neutral-950">
        <Container>
          <div className="flex h-16 items-center justify-between">
            <span className="font-display text-lg font-medium tracking-tight text-white">DivAi</span>
            <div className="flex items-center gap-4">
              {authedUser ? (
                <Link
                  href="/history"
                  className="inline-flex items-center gap-1.5 text-xs font-medium text-neutral-400 hover:text-white transition"
                >
                  <History className="w-3.5 h-3.5" /> My Reports
                </Link>
              ) : (
                <Link
                  href="/login"
                  className="text-xs font-medium text-neutral-400 hover:text-white transition"
                >
                  Sign in
                </Link>
              )}
              <span className="text-xs font-medium tracking-widest uppercase text-neutral-500 hidden sm:block">AI Lead Intelligence</span>
            </div>
          </div>
        </Container>
      </header>

      {/* Hero */}
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
              DivAi scrapes, analyses, and writes a full technical proposal for any website — in under 5 minutes.
            </p>
          </FadeIn>

          <FadeIn>
            <div ref={formRef} className="mt-12 max-w-2xl">

              {/* Step 1 — URL */}
              {step === "url" && (
                <form onSubmit={handleUrlSubmit}>
                  <div className="flex flex-col gap-3 sm:flex-row">
                    <input
                      type="url"
                      value={url}
                      onChange={e => setUrl(e.target.value)}
                      placeholder="https://stripe.com"
                      required
                      className="flex-1 rounded-2xl border border-neutral-700 bg-neutral-900 px-6 py-4 text-white placeholder-neutral-600 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition"
                    />
                    <button
                      type="submit"
                      disabled={loading}
                      className="inline-flex items-center gap-2 rounded-2xl bg-blue-600 px-8 py-4 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition shrink-0"
                    >
                      {loading ? (
                        <><span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" /> Starting…</>
                      ) : (
                        <>Continue <ArrowRight className="h-4 w-4" /></>
                      )}
                    </button>
                  </div>
                  <p className="mt-4 text-sm text-neutral-600">
                    Site behind a login?{" "}
                    <Link
                      href={url ? `/auth-capture?url=${encodeURIComponent(url)}` : "/auth-capture"}
                      className="inline-flex items-center gap-1 text-neutral-400 hover:text-white transition"
                    >
                      <KeyRound className="h-3.5 w-3.5" /> Sign up &amp; capture session first
                    </Link>
                  </p>
                </form>
              )}

              {/* Step 2 — Identity */}
              {step === "identity" && (
                <form onSubmit={handleIdentitySubmit} className="space-y-3">
                  <div className="rounded-2xl border border-neutral-700 bg-neutral-900 px-5 py-4">
                    <p className="text-xs text-neutral-500 mb-1">Analysing</p>
                    <p className="text-sm text-white truncate">{url}</p>
                  </div>

                  <p className="text-sm text-neutral-400 pt-1">Where should we send the proposal?</p>

                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    required
                    className="w-full rounded-2xl border border-neutral-700 bg-neutral-900 px-6 py-4 text-white placeholder-neutral-600 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition"
                  />

                  <div className="flex gap-3">
                    <div className="relative flex-1">
                      <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-600" />
                      <input
                        type="text"
                        value={name}
                        onChange={e => setName(e.target.value)}
                        placeholder="Your name"
                        className="w-full rounded-2xl border border-neutral-700 bg-neutral-900 pl-10 pr-5 py-4 text-white placeholder-neutral-600 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition"
                      />
                    </div>
                    <div className="relative flex-1">
                      <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-600" />
                      <input
                        type="text"
                        value={company}
                        onChange={e => setCompany(e.target.value)}
                        placeholder="Company (optional)"
                        className="w-full rounded-2xl border border-neutral-700 bg-neutral-900 pl-10 pr-5 py-4 text-white placeholder-neutral-600 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition"
                      />
                    </div>
                  </div>

                  {error && <p className="text-sm text-red-400">{error}</p>}

                  <div className="flex gap-3 pt-1">
                    <button
                      type="button"
                      onClick={() => { setStep("url"); setError(null); }}
                      className="rounded-2xl border border-neutral-700 px-6 py-4 text-sm text-neutral-400 hover:border-neutral-500 cursor-pointer transition"
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-1 inline-flex items-center justify-center gap-2 rounded-2xl bg-blue-600 px-8 py-4 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
                    >
                      {loading ? (
                        <><span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" /> Starting…</>
                      ) : (
                        <>Analyse <ArrowRight className="h-4 w-4" /></>
                      )}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </FadeIn>
        </Container>
      </section>

      {/* Workflow animation */}
      <section className="border-t border-neutral-100 py-20 bg-white">
        <Container>
          <FadeIn>
            <div className="mb-10">
              <p className="text-xs font-medium uppercase tracking-widest text-neutral-400 mb-3">See it in action</p>
              <p className="font-display text-2xl font-semibold tracking-tight text-neutral-950">
                From URL to proposal — every step, animated.
              </p>
            </div>
          </FadeIn>
          <FadeIn>
            <WorkflowAnimation onStart={handleScrollToForm} />
          </FadeIn>
        </Container>
      </section>

      {/* Footer */}
      <footer className="border-t border-neutral-100 py-10">
        <Container>
          <div className="flex items-center justify-between">
            <span className="text-xs text-neutral-400">© {new Date().getFullYear()} DivAi. AI-powered business intelligence.</span>
            <span className="text-xs font-medium tracking-widest uppercase text-neutral-300">DiV Dynamics</span>
          </div>
        </Container>
      </footer>
    </div>
  );
}
