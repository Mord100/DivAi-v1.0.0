"use client";

import { useState, FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Loader2, Chrome } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

type Mode = "login" | "signup";

export default function LoginPage() {
  const searchParams = useSearchParams();
  const from         = searchParams.get("from") ?? "/history";
  const authError    = searchParams.get("error");

  const [mode, setMode]         = useState<Mode>("login");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading]   = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError]       = useState<string | null>(
    authError === "auth_failed" ? "Authentication failed. Please try again." : null
  );
  const [success, setSuccess]   = useState<string | null>(null);

  const supabase = createClient();

  async function handleEmailAuth(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    if (mode === "signup") {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${location.origin}/auth/callback?next=${from}`,
        },
      });
      if (error) {
        setError(error.message);
      } else {
        setSuccess("Check your email to confirm your account, then sign in.");
      }
    } else {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        setError(error.message);
      } else {
        // Hard redirect so middleware picks up the new session cookie
        window.location.href = from;
      }
    }

    setLoading(false);
  }

  async function handleGoogle() {
    setGoogleLoading(true);
    setError(null);
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${location.origin}/auth/callback?next=${from}`,
      },
    });
    if (error) {
      setError(error.message);
      setGoogleLoading(false);
    }
    // If no error, browser navigates away to Google
  }

  return (
    <main className="min-h-screen bg-[#0a0a0a] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">

        {/* Logo */}
        <div className="mb-10 text-center">
          <Link href="/" className="font-display text-2xl font-semibold tracking-tight text-white hover:text-neutral-300 transition">
            DivAi
          </Link>
          <p className="mt-1 text-xs text-neutral-600 uppercase tracking-widest">
            {mode === "login" ? "Sign in to your account" : "Create an account"}
          </p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-8 space-y-5">

          {/* Google */}
          <button
            onClick={handleGoogle}
            disabled={googleLoading}
            className="w-full flex items-center justify-center gap-3 rounded-xl border border-neutral-700 bg-neutral-800 px-4 py-3 text-sm font-medium text-neutral-200 hover:bg-neutral-700 hover:border-neutral-600 disabled:opacity-40 transition"
          >
            {googleLoading
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Chrome className="w-4 h-4" />
            }
            Continue with Google
          </button>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-neutral-800" />
            <span className="text-xs text-neutral-600">or</span>
            <div className="flex-1 h-px bg-neutral-800" />
          </div>

          {/* Email + password form */}
          <form onSubmit={handleEmailAuth} className="space-y-3">
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="Email"
              required
              autoFocus
              className="w-full rounded-xl border border-neutral-700 bg-neutral-800 px-4 py-3 text-sm text-white placeholder-neutral-600 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition"
            />
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Password"
              required
              minLength={6}
              className="w-full rounded-xl border border-neutral-700 bg-neutral-800 px-4 py-3 text-sm text-white placeholder-neutral-600 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition"
            />

            {error   && <p className="text-xs text-red-400">{error}</p>}
            {success && <p className="text-xs text-green-400">{success}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              {loading
                ? <><Loader2 className="w-4 h-4 animate-spin" /> {mode === "login" ? "Signing in…" : "Creating account…"}</>
                : mode === "login" ? "Sign in" : "Create account"
              }
            </button>
          </form>

          {/* Mode toggle */}
          <p className="text-center text-xs text-neutral-500">
            {mode === "login" ? (
              <>No account?{" "}
                <button onClick={() => { setMode("signup"); setError(null); setSuccess(null); }} className="text-blue-400 hover:text-blue-300 transition">
                  Sign up
                </button>
              </>
            ) : (
              <>Already have an account?{" "}
                <button onClick={() => { setMode("login"); setError(null); setSuccess(null); }} className="text-blue-400 hover:text-blue-300 transition">
                  Sign in
                </button>
              </>
            )}
          </p>
        </div>

        <p className="mt-6 text-center text-xs text-neutral-700">
          <Link href="/" className="hover:text-neutral-500 transition">← Back to DivAi</Link>
        </p>
      </div>
    </main>
  );
}
