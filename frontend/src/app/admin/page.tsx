"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FadeIn } from "@/components/FadeIn";
import { Container } from "@/components/Container";
import { ArrowRight, Globe, Loader2, Users, TrendingUp, DollarSign, Download, RefreshCw, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface UserRef { email?: string; name?: string; company?: string; }

interface Scan {
  id: string; url: string; depth: string; status: string;
  current_stage: string | null; error: string | null;
  lead_score: number | null; paid: boolean | null;
  promo_code_used: string | null; root_url: string | null;
  created_at: string; updated_at: string; users?: UserRef | null;
}

interface TopLead {
  id: string; url: string; lead_score: number;
  status: string; created_at: string; users?: UserRef | null;
}

interface Stats {
  total_scans: number; by_status: Record<string, number>;
  completion_rate: number; total_users: number;
  paid_scans: number; conversion_rate: number;
  proposal_downloads: number; avg_lead_score: number;
  top_leads: TopLead[];
}

const STATUS_MAP: Record<string, { label: string; dot: string }> = {
  complete:       { label: "Complete",  dot: "bg-green-500" },
  running:        { label: "Running",   dot: "bg-blue-500 animate-pulse" },
  pending:        { label: "Pending",   dot: "bg-neutral-500" },
  awaiting_input: { label: "Waiting",   dot: "bg-yellow-500" },
  error:          { label: "Error",     dot: "bg-red-500" },
};

function StatusDot({ status }: { status: string }) {
  const { label, dot } = STATUS_MAP[status] ?? { label: status, dot: "bg-neutral-500" };
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-neutral-400">
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dot}`} />
      {label}
    </span>
  );
}

function ScoreRing({ score }: { score: number | null }) {
  if (score == null) return <span className="text-neutral-700 text-xs tabular-nums">—</span>;
  const color = score >= 60 ? "text-green-400" : score >= 30 ? "text-yellow-400" : "text-neutral-500";
  return (
    <span className={`font-display text-base font-semibold tabular-nums ${color}`}>{score}</span>
  );
}

function StatCard({ label, value, sub, icon, accent }: {
  label: string; value: string | number; sub?: string;
  icon?: React.ReactNode; accent?: boolean;
}) {
  return (
    <div className={`relative rounded-2xl border p-5 overflow-hidden ${accent ? "border-blue-500/30 bg-blue-950/20" : "border-neutral-800 bg-neutral-900"}`}>
      {accent && <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />}
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs text-neutral-500 uppercase tracking-wider">{label}</p>
        {icon && <span className="text-neutral-600 shrink-0">{icon}</span>}
      </div>
      <p className={`mt-3 font-display text-4xl font-semibold tabular-nums ${accent ? "text-blue-400" : "text-white"}`}>
        {value}
      </p>
      {sub && <p className="mt-1 text-xs text-neutral-500">{sub}</p>}
    </div>
  );
}

export default function AdminPage() {
  const [stats, setStats]     = useState<Stats | null>(null);
  const [scans, setScans]     = useState<Scan[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const router = useRouter();

  async function logout() {
    await fetch("/api/admin-auth", { method: "DELETE" });
    router.push("/admin/login");
  }

  async function load(isRefresh = false) {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    const [statsRes, scansRes] = await Promise.all([
      fetch(`${API_URL}/api/admin/stats`),
      fetch(`${API_URL}/api/admin/scans?page_size=50${statusFilter ? `&status=${statusFilter}` : ""}`),
    ]);
    setStats(await statsRes.json());
    const data = await scansRes.json();
    setScans(data.scans ?? []);
    if (isRefresh) setRefreshing(false); else setLoading(false);
  }

  useEffect(() => { load(); }, [statusFilter]);

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white">

      {/* Top bar */}
      <header className="border-b border-neutral-800/60 bg-[#0a0a0a] sticky top-0 z-10 backdrop-blur-sm">
        <Container>
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-8">
              <Link href="/" className="font-display text-base font-semibold tracking-tight text-white hover:text-neutral-300 transition">
                DivAi
              </Link>
              <nav className="flex items-center gap-1">
                <span className="rounded-full bg-neutral-800 px-3.5 py-1 text-sm font-medium text-white">
                  Scans
                </span>
                <Link
                  href="/admin/users"
                  className="rounded-full px-3.5 py-1 text-sm font-medium text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800/60 transition"
                >
                  Users
                </Link>
              </nav>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => load(true)}
                disabled={refreshing}
                className="flex items-center gap-2 rounded-full border border-neutral-700 px-4 py-1.5 text-xs font-medium text-neutral-400 hover:border-neutral-500 hover:text-neutral-200 transition disabled:opacity-40"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
                Refresh
              </button>
              <button
                onClick={logout}
                className="flex items-center gap-2 rounded-full border border-neutral-800 px-3 py-1.5 text-xs text-neutral-600 hover:text-neutral-400 hover:border-neutral-700 cursor-pointer transition"
                title="Sign out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </Container>
      </header>

      <Container>
        <div className="py-10 space-y-10">

          {/* Stat cards */}
          <FadeIn>
            {stats ? (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
                <StatCard label="Total Scans" value={stats.total_scans} sub={`${stats.completion_rate}% complete`} accent />
                <StatCard label="Users" value={stats.total_users} icon={<Users className="w-4 h-4" />} />
                <StatCard label="Paid" value={stats.paid_scans} sub={`${stats.conversion_rate}% conv.`} icon={<DollarSign className="w-4 h-4" />} />
                <StatCard label="Downloads" value={stats.proposal_downloads} icon={<Download className="w-4 h-4" />} />
                <StatCard label="Avg Score" value={stats.avg_lead_score} icon={<TrendingUp className="w-4 h-4" />} />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-28 rounded-2xl border border-neutral-800 bg-neutral-900 animate-pulse" />
                ))}
              </div>
            )}
          </FadeIn>

          {/* Top leads */}
          {stats?.top_leads && stats.top_leads.length > 0 && (
            <FadeIn>
              <div className="rounded-2xl border border-neutral-800 bg-neutral-900 overflow-hidden">
                <div className="px-6 py-3.5 border-b border-neutral-800 flex items-center justify-between">
                  <p className="text-xs font-medium uppercase tracking-widest text-neutral-500">Top Leads</p>
                </div>
                <div className="divide-y divide-neutral-800/60">
                  {stats.top_leads.map((lead, i) => (
                    <div key={lead.id} className="flex items-center gap-4 px-6 py-3.5 hover:bg-neutral-800/40 transition group">
                      <span className="w-5 shrink-0 text-xs text-neutral-600 tabular-nums text-right">{i + 1}</span>
                      <ScoreRing score={lead.lead_score} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-neutral-200 truncate">{lead.url}</p>
                        {lead.users?.email && (
                          <p className="text-xs text-neutral-600 truncate mt-0.5">{lead.users.email}</p>
                        )}
                      </div>
                      <StatusDot status={lead.status} />
                      <Link
                        href={`/admin/scans/${lead.id}`}
                        className="shrink-0 opacity-0 group-hover:opacity-100 transition inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
                      >
                        View <ArrowRight className="w-3 h-3" />
                      </Link>
                    </div>
                  ))}
                </div>
              </div>
            </FadeIn>
          )}

          {/* Scans table */}
          <FadeIn>
            <div className="rounded-2xl border border-neutral-800 bg-neutral-900 overflow-hidden">
              <div className="flex items-center justify-between px-6 py-3.5 border-b border-neutral-800">
                <p className="text-xs font-medium uppercase tracking-widest text-neutral-500">All Scans</p>
                <select
                  value={statusFilter}
                  onChange={e => setStatusFilter(e.target.value)}
                  className="rounded-full border border-neutral-700 bg-neutral-800 px-3 py-1 text-xs text-neutral-300 focus:outline-none focus:border-neutral-500 transition"
                >
                  <option value="">All statuses</option>
                  <option value="complete">Complete</option>
                  <option value="error">Error</option>
                  <option value="pending">Pending</option>
                  <option value="running">Running</option>
                  <option value="awaiting_input">Waiting</option>
                </select>
              </div>

              {loading ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="w-5 h-5 animate-spin text-neutral-700" />
                </div>
              ) : scans.length === 0 ? (
                <p className="py-20 text-center text-sm text-neutral-600">No scans found.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-neutral-800/60">
                        <th className="px-6 py-3 text-left text-xs font-medium text-neutral-600">Score</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-neutral-600">Target</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-neutral-600">Status</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-neutral-600 hidden sm:table-cell">Paid</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-neutral-600 hidden md:table-cell">Date</th>
                        <th className="px-4 py-3" />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-800/50">
                      {scans.map(scan => (
                        <tr key={scan.id} className="hover:bg-neutral-800/30 transition group">
                          <td className="px-6 py-3.5">
                            <ScoreRing score={scan.lead_score} />
                          </td>
                          <td className="px-4 py-3.5">
                            <div className="flex items-start gap-2">
                              <Globe className="w-3.5 h-3.5 text-neutral-600 shrink-0 mt-0.5" />
                              <div className="min-w-0">
                                <p className="text-sm text-neutral-200 truncate max-w-[220px]">{scan.url}</p>
                                {scan.users?.email && (
                                  <p className="text-xs text-neutral-600 truncate mt-0.5">{scan.users.email}</p>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3.5">
                            <StatusDot status={scan.status} />
                          </td>
                          <td className="px-4 py-3.5 hidden sm:table-cell">
                            {scan.paid
                              ? <span className="text-xs font-medium text-green-400">Paid</span>
                              : <span className="text-xs text-neutral-700">—</span>
                            }
                          </td>
                          <td className="px-4 py-3.5 hidden md:table-cell text-xs text-neutral-600">
                            {new Date(scan.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3.5 text-right">
                            <Link
                              href={`/admin/scans/${scan.id}`}
                              className="opacity-0 group-hover:opacity-100 transition inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
                            >
                              View <ArrowRight className="w-3 h-3" />
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </FadeIn>

        </div>
      </Container>
    </main>
  );
}
