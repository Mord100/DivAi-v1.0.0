"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Container } from "@/components/Container";
import { FadeIn, FadeInStagger } from "@/components/FadeIn";
import { createClient } from "@/lib/supabase/client";
import { useAuth } from "@/lib/supabase/AuthProvider";
import {
  ArrowRight, Globe, Loader2, LogOut, Plus,
  CheckCircle, Clock, AlertCircle, Hourglass,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface UserScan {
  id: string;
  url: string;
  status: string;
  lead_score: number | null;
  paid: boolean | null;
  created_at: string;
  current_stage: string | null;
  proposal_paths: { title?: string; signed_url?: string } | null;
}

interface UserProfile {
  id: string;
  email: string;
  name: string | null;
  company: string | null;
}

const STATUS_CONFIG: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  complete:       { label: "Complete",  icon: <CheckCircle className="w-3.5 h-3.5" />, color: "text-green-400" },
  running:        { label: "Running",   icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />, color: "text-blue-400" },
  awaiting_input: { label: "Your turn", icon: <Hourglass className="w-3.5 h-3.5" />, color: "text-yellow-400" },
  pending:        { label: "Queued",    icon: <Clock className="w-3.5 h-3.5" />, color: "text-neutral-500" },
  error:          { label: "Failed",    icon: <AlertCircle className="w-3.5 h-3.5" />, color: "text-red-400" },
};

function ScanCard({ scan }: { scan: UserScan }) {
  const cfg = STATUS_CONFIG[scan.status] ?? { label: scan.status, icon: null, color: "text-neutral-400" };
  const isComplete = scan.status === "complete";
  const isActive   = scan.status === "running" || scan.status === "awaiting_input";
  const score      = scan.lead_score;
  const scoreColor = score != null
    ? score >= 60 ? "text-green-400" : score >= 30 ? "text-yellow-400" : "text-neutral-500"
    : "text-neutral-700";

  return (
    <div className={`rounded-2xl border bg-neutral-900 p-5 transition ${isActive ? "border-blue-500/30" : "border-neutral-800"}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 min-w-0">
          <Globe className="w-4 h-4 text-neutral-600 shrink-0 mt-0.5" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-neutral-200 truncate">{scan.url}</p>
            {scan.proposal_paths?.title && (
              <p className="text-xs text-neutral-500 mt-0.5 truncate">{scan.proposal_paths.title}</p>
            )}
            <p className="text-xs text-neutral-700 mt-1">
              {new Date(scan.created_at).toLocaleDateString("en-GB", {
                day: "numeric", month: "short", year: "numeric",
              })}
            </p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <div className={`flex items-center gap-1.5 text-xs font-medium ${cfg.color}`}>
            {cfg.icon}
            {cfg.label}
          </div>
          {score != null && (
            <span className={`font-display text-sm font-semibold tabular-nums ${scoreColor}`}>
              {score}
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="mt-4 flex items-center gap-3">
        {isComplete && (
          <Link
            href={`/report/${scan.id}`}
            className="inline-flex items-center gap-1.5 rounded-full bg-neutral-800 hover:bg-neutral-700 px-4 py-1.5 text-xs font-medium text-neutral-200 transition"
          >
            View report <ArrowRight className="w-3 h-3" />
          </Link>
        )}
        {isActive && (
          <Link
            href={`/scan/${scan.id}`}
            className="inline-flex items-center gap-1.5 rounded-full bg-blue-600 hover:bg-blue-500 px-4 py-1.5 text-xs font-medium text-white transition"
          >
            Continue <ArrowRight className="w-3 h-3" />
          </Link>
        )}
        {scan.proposal_paths?.signed_url && (
          <a
            href={scan.proposal_paths.signed_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-neutral-500 hover:text-neutral-300 transition"
          >
            Download .docx
          </a>
        )}
        {scan.paid && (
          <span className="ml-auto text-xs font-medium text-green-400">Paid</span>
        )}
      </div>
    </div>
  );
}

export default function HistoryPage() {
  const router   = useRouter();
  const supabase = createClient();
  const { user: authUser, loading: authLoading } = useAuth();

  const [user, setUser]       = useState<UserProfile | null>(null);
  const [scans, setScans]     = useState<UserScan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;  // wait for auth context to resolve

    async function load() {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push("/login?from=/history");
        return;
      }

      const res = await fetch(`${API_URL}/api/me/scans`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
        setScans(data.scans);
      }

      setLoading(false);
    }

    load();
  }, [authLoading]);

  async function signOut() {
    await supabase.auth.signOut();
    router.push("/");
  }

  const completed = scans.filter(s => s.status === "complete").length;
  const active    = scans.filter(s => s.status === "running" || s.status === "awaiting_input").length;

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white">

      {/* Header */}
      <header className="border-b border-neutral-800/60 bg-[#0a0a0a] sticky top-0 z-10 backdrop-blur-sm">
        <Container>
          <div className="flex items-center justify-between h-14">
            <Link href="/" className="font-display text-base font-semibold tracking-tight text-white hover:text-neutral-300 transition">
              DivAi
            </Link>
            <div className="flex items-center gap-3">
              {user && (
                <span className="text-xs text-neutral-500 hidden sm:block">{user.email}</span>
              )}
              <Link
                href="/"
                className="inline-flex items-center gap-1.5 rounded-full bg-blue-600 hover:bg-blue-500 px-4 py-1.5 text-xs font-semibold text-white transition"
              >
                <Plus className="w-3.5 h-3.5" /> New scan
              </Link>
              <button
                onClick={signOut}
                className="p-1.5 text-neutral-600 hover:text-neutral-400 cursor-pointer transition"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </Container>
      </header>

      <Container>
        <div className="py-10">

          {loading ? (
            <div className="flex items-center justify-center py-32">
              <Loader2 className="w-6 h-6 animate-spin text-neutral-700" />
            </div>
          ) : (
            <>
              {/* Welcome */}
              <FadeIn>
                <div className="mb-10">
                  <h1 className="font-display text-3xl font-semibold tracking-tight">
                    {user?.name ? `Hey, ${user.name.split(" ")[0]}` : "My Reports"}
                  </h1>
                  <p className="mt-2 text-sm text-neutral-500">
                    {scans.length === 0
                      ? "No scans yet. Start by entering a URL."
                      : `${completed} completed · ${scans.length - completed} in progress`}
                  </p>
                </div>
              </FadeIn>

              {/* Active scans */}
              {active > 0 && (
                <FadeIn>
                  <div className="mb-8">
                    <p className="text-xs font-medium uppercase tracking-widest text-neutral-600 mb-3">In progress</p>
                    <div className="space-y-3">
                      {scans
                        .filter(s => s.status === "running" || s.status === "awaiting_input")
                        .map(scan => <ScanCard key={scan.id} scan={scan} />)
                      }
                    </div>
                  </div>
                </FadeIn>
              )}

              {/* All scans */}
              {scans.length === 0 ? (
                <FadeIn>
                  <div className="rounded-2xl border border-neutral-800 border-dashed p-12 text-center">
                    <p className="text-sm text-neutral-600 mb-4">No scans yet.</p>
                    <Link
                      href="/"
                      className="inline-flex items-center gap-2 rounded-full bg-blue-600 hover:bg-blue-500 px-5 py-2.5 text-sm font-semibold text-white transition"
                    >
                      <Plus className="w-4 h-4" /> Start your first scan
                    </Link>
                  </div>
                </FadeIn>
              ) : (
                <div>
                  <p className="text-xs font-medium uppercase tracking-widest text-neutral-600 mb-3">All scans</p>
                  <FadeInStagger faster>
                    <div className="space-y-3">
                      {scans.map(scan => (
                        <FadeIn key={scan.id}>
                          <ScanCard scan={scan} />
                        </FadeIn>
                      ))}
                    </div>
                  </FadeInStagger>
                </div>
              )}
            </>
          )}

        </div>
      </Container>
    </main>
  );
}
