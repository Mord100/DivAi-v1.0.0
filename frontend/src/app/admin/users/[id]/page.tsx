"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FadeIn, FadeInStagger } from "@/components/FadeIn";
import { Container } from "@/components/Container";
import { ArrowLeft, ArrowRight, Building2, Mail, Loader2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface User { id: string; email: string; name: string | null; company: string | null; created_at: string; updated_at: string; }
interface UserScan { id: string; url: string; status: string; lead_score: number | null; paid: boolean | null; promo_code_used: string | null; created_at: string; }
interface UserEvent { scan_id: string; event_type: string; metadata: Record<string, unknown>; created_at: string; }
interface UserDetail { user: User; scans: UserScan[]; events: UserEvent[]; }

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

const EVENT_LABELS: Record<string, string> = {
  report_viewed:       "Viewed report",
  proposal_downloaded: "Downloaded proposal",
  tab_switched:        "Switched tab",
  scan_started:        "Started scan",
  use_case_selected:   "Selected use cases",
  solution_selected:   "Selected solution",
};

export default function UserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData]     = useState<UserDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/admin/users/${id}`)
      .then(r => r.ok ? r.json() : Promise.reject("Not found"))
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(String(e)); setLoading(false); });
  }, [id]);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-neutral-700" />
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="min-h-screen bg-[#0a0a0a] text-white flex items-center justify-center">
        <p className="text-neutral-600 text-sm">{error ?? "User not found"}</p>
      </main>
    );
  }

  const { user, scans, events } = data;
  const topScore  = Math.max(0, ...scans.map(sc => sc.lead_score ?? 0));
  const paid      = scans.filter(sc => sc.paid).length;
  const completed = scans.filter(sc => sc.status === "complete").length;

  const scoreColor = topScore >= 60 ? "text-green-400" : topScore >= 30 ? "text-yellow-400" : "text-neutral-400";

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white">

      <header className="border-b border-neutral-800/60 bg-[#0a0a0a] sticky top-0 z-10 backdrop-blur-sm">
        <Container>
          <div className="flex items-center gap-4 h-14">
            <Link href="/admin/users" className="text-neutral-600 hover:text-neutral-300 transition">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="h-4 w-px bg-neutral-800" />
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-xs text-neutral-600">Users</span>
              <span className="text-neutral-700">/</span>
              <span className="text-sm font-medium text-neutral-200 truncate">{user.name ?? user.email}</span>
            </div>
          </div>
        </Container>
      </header>

      <Container>
        <div className="py-10 space-y-6">

          {/* Profile + stats */}
          <FadeIn>
            <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-6">
                {/* Identity */}
                <div className="space-y-2">
                  {user.name && (
                    <h1 className="font-display text-2xl font-semibold tracking-tight">{user.name}</h1>
                  )}
                  <div className="flex items-center gap-2 text-sm text-neutral-400">
                    <Mail className="w-3.5 h-3.5 text-neutral-600" />
                    {user.email}
                  </div>
                  {user.company && (
                    <div className="flex items-center gap-2 text-sm text-neutral-400">
                      <Building2 className="w-3.5 h-3.5 text-neutral-600" />
                      {user.company}
                    </div>
                  )}
                  <p className="text-xs text-neutral-700 pt-1">
                    Joined {new Date(user.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}
                  </p>
                </div>

                {/* Quick stats */}
                <div className="flex gap-6 sm:gap-8 shrink-0">
                  {[
                    { label: "Scans",     value: scans.length, color: "text-white" },
                    { label: "Completed", value: completed,    color: "text-white" },
                    { label: "Paid",      value: paid,         color: paid > 0 ? "text-green-400" : "text-neutral-500" },
                    { label: "Top Score", value: topScore || "—", color: topScore > 0 ? scoreColor : "text-neutral-500" },
                  ].map(stat => (
                    <div key={stat.label} className="text-center">
                      <p className={`font-display text-3xl font-semibold tabular-nums ${stat.color}`}>{stat.value}</p>
                      <p className="text-xs text-neutral-600 mt-1">{stat.label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </FadeIn>

          {/* Scans */}
          <FadeIn>
            <div className="rounded-2xl border border-neutral-800 bg-neutral-900 overflow-hidden">
              <div className="px-6 py-3.5 border-b border-neutral-800">
                <p className="text-xs font-medium uppercase tracking-widest text-neutral-500">
                  Scans <span className="text-neutral-700 ml-1">{scans.length}</span>
                </p>
              </div>
              {scans.length === 0 ? (
                <p className="py-16 text-center text-sm text-neutral-600">No scans yet.</p>
              ) : (
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-neutral-800/60">
                      <th className="px-6 py-3 text-left text-xs font-medium text-neutral-600">Score</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-neutral-600">URL</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-neutral-600">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-neutral-600 hidden sm:table-cell">Paid</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-neutral-600 hidden md:table-cell">Date</th>
                      <th className="px-4 py-3" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-800/50">
                    {scans.map(scan => {
                      const sc = scan.lead_score;
                      const col = sc != null ? (sc >= 60 ? "text-green-400" : sc >= 30 ? "text-yellow-400" : "text-neutral-500") : "text-neutral-700";
                      return (
                        <tr key={scan.id} className="hover:bg-neutral-800/30 transition group">
                          <td className="px-6 py-3.5">
                            <span className={`font-display text-base font-semibold tabular-nums ${col}`}>
                              {sc ?? "—"}
                            </span>
                          </td>
                          <td className="px-4 py-3.5 text-sm text-neutral-200 truncate max-w-[220px]">{scan.url}</td>
                          <td className="px-4 py-3.5"><StatusDot status={scan.status} /></td>
                          <td className="px-4 py-3.5 hidden sm:table-cell">
                            {scan.paid
                              ? <span className="text-xs font-medium text-green-400">Paid{scan.promo_code_used ? ` · ${scan.promo_code_used}` : ""}</span>
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
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </FadeIn>

          {/* Events */}
          {events.length > 0 && (
            <FadeIn>
              <div className="rounded-2xl border border-neutral-800 bg-neutral-900 overflow-hidden">
                <div className="px-6 py-3.5 border-b border-neutral-800">
                  <p className="text-xs font-medium uppercase tracking-widest text-neutral-500">
                    Activity <span className="text-neutral-700 ml-1">{events.length}</span>
                  </p>
                </div>
                <FadeInStagger faster>
                  {events.map((ev, i) => (
                    <FadeIn key={i}>
                      <div className="flex items-start justify-between px-6 py-3.5 border-b border-neutral-800/40 last:border-0 hover:bg-neutral-800/20 transition">
                        <div className="flex items-start gap-3">
                          <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-500/60 shrink-0" />
                          <div>
                            <p className="text-sm text-neutral-300">{EVENT_LABELS[ev.event_type] ?? ev.event_type}</p>
                            <p className="text-xs text-neutral-700 font-mono mt-0.5">
                              {ev.scan_id.slice(0, 8)}…
                            </p>
                          </div>
                        </div>
                        <p className="text-xs text-neutral-600 shrink-0 ml-4">
                          {new Date(ev.created_at).toLocaleString()}
                        </p>
                      </div>
                    </FadeIn>
                  ))}
                </FadeInStagger>
              </div>
            </FadeIn>
          )}

        </div>
      </Container>
    </main>
  );
}
