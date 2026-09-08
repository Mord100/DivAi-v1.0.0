"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FadeIn } from "@/components/FadeIn";
import { Container } from "@/components/Container";
import { ArrowRight, Loader2, Building2, RefreshCw, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface User {
  id: string; email: string; name: string | null; company: string | null;
  created_at: string; scan_count: number; paid_count: number;
  top_score: number; completed: number;
}

function ScoreChip({ score }: { score: number }) {
  if (!score) return <span className="text-neutral-700 text-xs">—</span>;
  const color = score >= 60 ? "text-green-400" : score >= 30 ? "text-yellow-400" : "text-neutral-500";
  return <span className={`font-display text-base font-semibold tabular-nums ${color}`}>{score}</span>;
}

export default function AdminUsersPage() {
  const [users, setUsers]     = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage]       = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const router = useRouter();

  async function logout() {
    await fetch("/api/admin-auth", { method: "DELETE" });
    router.push("/admin/login");
  }

  async function load(p = 1, isRefresh = false) {
    if (isRefresh) { setRefreshing(true); setPage(1); } else setLoading(true);
    const res  = await fetch(`${API_URL}/api/admin/users?page=${p}&page_size=25`);
    const data = await res.json();
    const rows = data.users ?? [];
    setUsers(p === 1 ? rows : prev => [...prev, ...rows]);
    setHasMore(rows.length === 25);
    if (isRefresh) setRefreshing(false); else setLoading(false);
  }

  useEffect(() => { load(1); }, []);

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white">

      <header className="border-b border-neutral-800/60 bg-[#0a0a0a] sticky top-0 z-10 backdrop-blur-sm">
        <Container>
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-8">
              <Link href="/" className="font-display text-base font-semibold tracking-tight text-white hover:text-neutral-300 transition">
                DivAi
              </Link>
              <nav className="flex items-center gap-1">
                <Link
                  href="/admin"
                  className="rounded-full px-3.5 py-1 text-sm font-medium text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800/60 transition"
                >
                  Scans
                </Link>
                <span className="rounded-full bg-neutral-800 px-3.5 py-1 text-sm font-medium text-white">
                  Users
                </span>
              </nav>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => load(1, true)}
                disabled={refreshing}
                className="flex items-center gap-2 rounded-full border border-neutral-700 px-4 py-1.5 text-xs font-medium text-neutral-400 hover:border-neutral-500 hover:text-neutral-200 transition disabled:opacity-40"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
                Refresh
              </button>
              <button
                onClick={logout}
                className="flex items-center gap-2 rounded-full border border-neutral-800 px-3 py-1.5 text-xs text-neutral-600 hover:text-neutral-400 hover:border-neutral-700 transition"
                title="Sign out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </Container>
      </header>

      <Container>
        <div className="py-10">
          <FadeIn>
            <div className="rounded-2xl border border-neutral-800 bg-neutral-900 overflow-hidden">
              <div className="px-6 py-3.5 border-b border-neutral-800">
                <p className="text-xs font-medium uppercase tracking-widest text-neutral-500">Identified Users</p>
              </div>

              {loading ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="w-5 h-5 animate-spin text-neutral-700" />
                </div>
              ) : users.length === 0 ? (
                <p className="py-20 text-center text-sm text-neutral-600">No users yet.</p>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-neutral-800/60">
                          <th className="px-6 py-3 text-left text-xs font-medium text-neutral-600">User</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-neutral-600 hidden md:table-cell">Company</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-neutral-600">Scans</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-neutral-600 hidden sm:table-cell">Done</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-neutral-600">Paid</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-neutral-600">Top</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-neutral-600 hidden lg:table-cell">Joined</th>
                          <th className="px-4 py-3" />
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-800/50">
                        {users.map(user => (
                          <tr key={user.id} className="hover:bg-neutral-800/30 transition group">
                            <td className="px-6 py-3.5">
                              {user.name && (
                                <p className="text-sm font-medium text-neutral-200">{user.name}</p>
                              )}
                              <p className={`text-xs ${user.name ? "text-neutral-500" : "text-neutral-300"} truncate max-w-[200px]`}>
                                {user.email}
                              </p>
                            </td>
                            <td className="px-4 py-3.5 hidden md:table-cell">
                              {user.company ? (
                                <span className="inline-flex items-center gap-1.5 text-xs text-neutral-400">
                                  <Building2 className="w-3 h-3 text-neutral-600" />{user.company}
                                </span>
                              ) : <span className="text-neutral-700 text-xs">—</span>}
                            </td>
                            <td className="px-4 py-3.5 text-right text-sm text-neutral-300 tabular-nums">{user.scan_count}</td>
                            <td className="px-4 py-3.5 text-right text-sm text-neutral-500 tabular-nums hidden sm:table-cell">{user.completed}</td>
                            <td className="px-4 py-3.5 text-right">
                              {user.paid_count > 0
                                ? <span className="text-sm font-medium text-green-400 tabular-nums">{user.paid_count}</span>
                                : <span className="text-neutral-700 text-xs">—</span>
                              }
                            </td>
                            <td className="px-4 py-3.5 text-right">
                              <ScoreChip score={user.top_score} />
                            </td>
                            <td className="px-4 py-3.5 text-xs text-neutral-600 hidden lg:table-cell">
                              {new Date(user.created_at).toLocaleDateString()}
                            </td>
                            <td className="px-4 py-3.5 text-right">
                              <Link
                                href={`/admin/users/${user.id}`}
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

                  {hasMore && (
                    <div className="px-6 py-4 border-t border-neutral-800/60">
                      <button
                        onClick={() => { const next = page + 1; setPage(next); load(next); }}
                        disabled={loading}
                        className="text-xs text-blue-400 hover:text-blue-300 transition disabled:opacity-40"
                      >
                        {loading ? "Loading…" : "Load more"}
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </FadeIn>
        </div>
      </Container>
    </main>
  );
}
