"use client";

import { useState, FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, Lock } from "lucide-react";

export default function AdminLoginPage() {
  const router       = useRouter();
  const searchParams = useSearchParams();
  const from         = searchParams.get("from") ?? "/admin";

  const [password, setPassword] = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const res = await fetch("/api/admin-auth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });

    if (res.ok) {
      router.push(from);
    } else {
      const data = await res.json();
      setError(data.error ?? "Invalid password");
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#0a0a0a] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">

        {/* Logo */}
        <div className="mb-10 text-center">
          <span className="font-display text-2xl font-semibold tracking-tight text-white">DivAi</span>
          <p className="mt-1 text-xs text-neutral-600 uppercase tracking-widest">Admin access</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-8">
          <div className="flex items-center justify-center w-10 h-10 rounded-full bg-neutral-800 mb-6">
            <Lock className="w-4 h-4 text-neutral-400" />
          </div>

          <h1 className="font-display text-xl font-semibold tracking-tight text-white mb-1">
            Sign in
          </h1>
          <p className="text-sm text-neutral-500 mb-6">Enter your admin password to continue.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Password"
              required
              autoFocus
              className="w-full rounded-xl border border-neutral-700 bg-neutral-800 px-4 py-3 text-sm text-white placeholder-neutral-600 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition"
            />

            {error && (
              <p className="text-xs text-red-400">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading || !password}
              className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              {loading
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Signing in…</>
                : "Sign in"
              }
            </button>
          </form>
        </div>

      </div>
    </main>
  );
}
