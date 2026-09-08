"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Container } from "@/components/Container";
import { FadeIn } from "@/components/FadeIn";
import {
  ArrowLeft, FileText, Lightbulb, Layers, Download,
  Loader2, Activity, CheckSquare
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Tab = "report" | "use_cases" | "solutions" | "proposal" | "log" | "selections";

export default function ScanDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData]       = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab]         = useState<Tab>("report");

  useEffect(() => {
    fetch(`${API_URL}/api/admin/scans/${id}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); });
  }, [id]);

  const scan    = data?.scan;
  const results = data?.results;

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: "report",     label: "Intelligence Report", icon: <FileText className="w-4 h-4" /> },
    { key: "use_cases",  label: "Use Cases",           icon: <Lightbulb className="w-4 h-4" /> },
    { key: "solutions",  label: "Solutions",           icon: <Layers className="w-4 h-4" /> },
    { key: "proposal",   label: "Proposal",            icon: <Download className="w-4 h-4" /> },
    { key: "selections", label: "Selections",          icon: <CheckSquare className="w-4 h-4" /> },
    { key: "log",        label: "Pipeline Log",        icon: <Activity className="w-4 h-4" /> },
  ];

  const STATUS_DOT: Record<string, string> = {
    complete: "bg-green-500", running: "bg-blue-500 animate-pulse",
    pending: "bg-neutral-500", awaiting_input: "bg-yellow-500", error: "bg-red-500",
  };

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white">

      {/* Top bar */}
      <header className="border-b border-neutral-800/60 bg-[#0a0a0a] sticky top-0 z-10 backdrop-blur-sm">
        <Container>
          <div className="flex items-center gap-4 h-14">
            <Link href="/admin" className="text-neutral-600 hover:text-neutral-300 transition">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="h-4 w-px bg-neutral-800" />
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <span className="text-xs text-neutral-600">Scans</span>
              <span className="text-neutral-700">/</span>
              <span className="text-sm text-neutral-200 truncate">{scan?.url ?? id}</span>
            </div>
            {scan && (
              <div className="flex items-center gap-3 shrink-0">
                {scan.lead_score != null && (
                  <span className={`font-display text-sm font-semibold tabular-nums ${scan.lead_score >= 60 ? "text-green-400" : scan.lead_score >= 30 ? "text-yellow-400" : "text-neutral-500"}`}>
                    {scan.lead_score}
                  </span>
                )}
                <span className="inline-flex items-center gap-1.5 text-xs text-neutral-400">
                  <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[scan.status] ?? "bg-neutral-500"}`} />
                  {scan.status}
                </span>
                {scan.paid && (
                  <span className="text-xs font-medium text-green-400">Paid</span>
                )}
              </div>
            )}
          </div>
        </Container>
      </header>

      <Container>
        <div className="py-8">
          {loading ? (
            <div className="flex items-center justify-center py-24">
              <Loader2 className="w-5 h-5 animate-spin text-neutral-700" />
            </div>
          ) : !results ? (
            <div className="py-24 text-center">
              <p className="text-sm text-neutral-600">No results for this scan yet.</p>
              <p className="text-xs text-neutral-700 mt-2">Status: {scan?.status}</p>
            </div>
          ) : (
            <FadeIn>
              {/* Pill tabs */}
              <div className="flex gap-1 mb-8 overflow-x-auto pb-1 scrollbar-hide">
                {tabs.map(t => (
                  <button
                    key={t.key}
                    onClick={() => setTab(t.key)}
                    className={`flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition ${
                      tab === t.key
                        ? "bg-neutral-800 text-white"
                        : "text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800/50"
                    }`}
                  >
                    {t.icon}{t.label}
                  </button>
                ))}
              </div>

              {tab === "report"     && <ReportTab report={results.intelligence_report} />}
              {tab === "use_cases"  && <UseCasesTab useCases={results.use_cases} />}
              {tab === "solutions"  && <SolutionsTab solutions={results.solutions} />}
              {tab === "proposal"   && <ProposalTab paths={results.proposal_paths} />}
              {tab === "selections" && <SelectionsTab scan={scan} useCases={results.use_cases} solutions={results.solutions} />}
              {tab === "log"        && <LogTab log={results.pipeline_log} />}
            </FadeIn>
          )}
        </div>
      </Container>
    </main>
  );
}

/* ── Shared primitives ───────────────────────────────────────────────────── */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-neutral-800/80 bg-neutral-900 p-5">
      <p className="text-xs font-medium text-neutral-600 uppercase tracking-widest mb-3">{title}</p>
      {children}
    </div>
  );
}

function Tags({ items }: { items: string[] }) {
  if (!items?.length) return <p className="text-sm text-neutral-500">None detected.</p>;
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((t, i) => (
        <span key={i} className="px-2.5 py-1 rounded-full bg-neutral-800 text-xs text-neutral-300">{t}</span>
      ))}
    </div>
  );
}

function KV({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs text-neutral-500">{label}</p>
      <p className="mt-0.5 text-sm text-white">{value ?? "—"}</p>
    </div>
  );
}

function Prose({ text }: { text: string }) {
  return <p className="text-sm text-neutral-400 leading-relaxed whitespace-pre-wrap">{text}</p>;
}

function Badge({ value, color = "neutral" }: { value: string; color?: "green" | "blue" | "yellow" | "red" | "neutral" }) {
  const colors = {
    green:   "bg-green-500/10 text-green-400 border-green-500/20",
    blue:    "bg-blue-500/10 text-blue-400 border-blue-500/20",
    yellow:  "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    red:     "bg-red-500/10 text-red-400 border-red-500/20",
    neutral: "bg-neutral-500/10 text-neutral-400 border-neutral-500/20",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${colors[color]}`}>
      {value}
    </span>
  );
}

/* ── Report Tab ──────────────────────────────────────────────────────────── */

function ReportTab({ report }: { report: any }) {
  if (!report) return <p className="text-neutral-500">No report data.</p>;
  const tech = report.tech_stack ?? {};
  const auth = report.auth_pattern ?? {};

  return (
    <div className="space-y-4">
      {/* Overview */}
      <Section title="Overview">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <KV label="Business Category" value={report.business_category} />
          <KV label="Frontend Framework" value={tech.frontend_framework} />
          <KV label="Language" value={tech.language} />
          <KV label="Stack Confidence" value={tech.confidence != null ? `${Math.round(tech.confidence * 100)}%` : "—"} />
          <KV label="API Endpoints Detected" value={report.api_endpoints?.length ?? 0} />
          <KV label="Key Features" value={report.key_features?.length ?? 0} />
        </div>
      </Section>

      {/* Tech Stack */}
      <Section title="Tech Stack Signals">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-neutral-500 mb-2">Hosting Signals</p>
            <Tags items={tech.hosting_signals ?? []} />
          </div>
          <div>
            <p className="text-xs text-neutral-500 mb-2">Database Signals</p>
            <Tags items={tech.database_signals ?? []} />
          </div>
        </div>
      </Section>

      {/* Auth Pattern */}
      <Section title="Auth Pattern">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-3">
          <KV label="Method" value={auth.method} />
          <KV label="Token Refresh" value={auth.token_refresh ? "Yes" : "No"} />
          <KV label="Providers" value={auth.providers?.join(", ") || "—"} />
        </div>
        {auth.notes && <Prose text={auth.notes} />}
      </Section>

      {/* API Endpoints */}
      {report.api_endpoints?.length > 0 && (
        <Section title={`API Endpoints (${report.api_endpoints.length})`}>
          <div className="space-y-3">
            {report.api_endpoints.map((ep: any, i: number) => (
              <div key={i} className="rounded-xl border border-neutral-700 bg-neutral-800/50 p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Badge value={ep.method} color="blue" />
                  <code className="text-xs text-neutral-200">{ep.url_pattern}</code>
                </div>
                <p className="text-xs text-neutral-400">{ep.inferred_purpose}</p>
                {ep.data_signals?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {ep.data_signals.map((s: string, j: number) => (
                      <span key={j} className="px-2 py-0.5 rounded bg-neutral-700 text-xs text-neutral-400">{s}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Key Features */}
      <Section title="Key Features"><Tags items={report.key_features ?? []} /></Section>

      {/* Integrations */}
      <Section title="Integrations"><Tags items={report.integrations ?? []} /></Section>

      {/* Data Models */}
      <Section title="Data Models"><Tags items={report.data_models ?? []} /></Section>

      {/* UI Patterns */}
      <Section title="UI Patterns"><Tags items={report.ui_patterns ?? []} /></Section>

      {/* Analyst Notes */}
      {report.analyst_notes && (
        <Section title="Analyst Notes"><Prose text={report.analyst_notes} /></Section>
      )}
    </div>
  );
}

/* ── Use Cases Tab ───────────────────────────────────────────────────────── */

function UseCasesTab({ useCases }: { useCases: any[] }) {
  if (!useCases?.length) return <p className="text-neutral-500">No use cases generated.</p>;
  return (
    <div className="space-y-4">
      {useCases.map((uc: any, i: number) => (
        <div key={i} className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5 space-y-3">
          <div className="flex items-start justify-between gap-4">
            <h3 className="font-medium text-white">{uc.title}</h3>
            <div className="flex shrink-0 items-center gap-2">
              <Badge value={uc.effort_estimate ?? "—"} color="yellow" />
              <Badge value={`${Math.round((uc.confidence_score ?? 0) * 100)}% confidence`} color="blue" />
            </div>
          </div>
          <p className="text-sm text-neutral-400">{uc.description}</p>
          {uc.supporting_evidence?.length > 0 && (
            <div>
              <p className="text-xs text-neutral-500 mb-2">Supporting Evidence</p>
              <ul className="space-y-1">
                {uc.supporting_evidence.map((ev: string, j: number) => (
                  <li key={j} className="flex gap-2 text-xs text-neutral-400">
                    <span className="text-neutral-600 shrink-0">—</span>{ev}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {uc.tags?.length > 0 && <Tags items={uc.tags} />}
        </div>
      ))}
    </div>
  );
}

/* ── Solutions Tab ───────────────────────────────────────────────────────── */

function SolutionsTab({ solutions }: { solutions: any[] }) {
  if (!solutions?.length) return <p className="text-neutral-500">No solutions generated.</p>;
  return (
    <div className="space-y-4">
      {solutions.map((sol: any, i: number) => (
        <div key={i} className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5 space-y-3">
          <div className="flex items-start justify-between gap-4">
            <h3 className="font-medium text-white">{sol.title}</h3>
            <div className="flex shrink-0 items-center gap-2">
              <Badge value={`Value: ${sol.value_score ?? "—"}`} color="green" />
              <Badge value={`Effort: ${sol.effort_score ?? "—"}`} color="yellow" />
              <Badge value={sol.timeline ?? "—"} color="neutral" />
            </div>
          </div>
          {sol.pitch && <p className="text-sm text-neutral-300 font-medium">{sol.pitch}</p>}
          {sol.architecture_overview && (
            <div>
              <p className="text-xs text-neutral-500 mb-1">Architecture Overview</p>
              <Prose text={sol.architecture_overview} />
            </div>
          )}
          {sol.stack?.length > 0 && (
            <div>
              <p className="text-xs text-neutral-500 mb-2">Tech Stack</p>
              <Tags items={sol.stack} />
            </div>
          )}
          {sol.risks?.length > 0 && (
            <div>
              <p className="text-xs text-neutral-500 mb-2">Risks</p>
              <ul className="space-y-1">
                {sol.risks.map((r: string, j: number) => (
                  <li key={j} className="flex gap-2 text-xs text-neutral-400">
                    <span className="text-red-500 shrink-0">!</span>{r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ── Proposal Tab ────────────────────────────────────────────────────────── */

function ProposalTab({ paths }: { paths: any }) {
  if (!paths) return <p className="text-neutral-500">No proposal generated.</p>;
  const c = paths.content ?? {};

  const sections = [
    { key: "executive_summary",   label: "Executive Summary" },
    { key: "problem_statement",   label: "Problem Statement" },
    { key: "proposed_architecture", label: "Proposed Architecture" },
    { key: "api_specifications",  label: "API Specifications" },
    { key: "testing_strategy",    label: "Testing Strategy" },
    { key: "deployment_devops",   label: "Deployment & DevOps" },
    { key: "security_compliance", label: "Security & Compliance" },
    { key: "investment_summary",  label: "Investment Summary" },
  ];

  return (
    <div className="space-y-4">
      {/* Header */}
      <Section title="Proposal Details">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <KV label="Project Title" value={paths.title} />
          <KV label="Client" value={paths.client} />
        </div>
        {paths.signed_url && (
          <a
            href={paths.signed_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-full bg-blue-600 hover:bg-blue-500 transition px-5 py-2.5 text-sm font-medium text-white"
          >
            <Download className="w-4 h-4" /> Download .docx
          </a>
        )}
      </Section>

      {/* Effort Table */}
      {c.effort_rows?.length > 0 && (
        <Section title="Effort Breakdown">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-neutral-500 border-b border-neutral-700">
                  <th className="pb-2 pr-4 font-medium">Role</th>
                  <th className="pb-2 pr-4 font-medium">Phase</th>
                  <th className="pb-2 pr-4 font-medium">Hours</th>
                  <th className="pb-2 pr-4 font-medium">Weeks</th>
                  <th className="pb-2 font-medium">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800">
                {c.effort_rows.map((row: any, i: number) => (
                  <tr key={i}>
                    <td className="py-2 pr-4 text-neutral-200">{row.role}</td>
                    <td className="py-2 pr-4 text-neutral-400 text-xs">{row.phase}</td>
                    <td className="py-2 pr-4 text-neutral-300">{row.hours}h</td>
                    <td className="py-2 pr-4 text-neutral-300">{row.weeks}w</td>
                    <td className="py-2 text-xs text-neutral-500">{row.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {/* Phase Details */}
      {c.phase_details?.length > 0 && (
        <Section title="Phase Details">
          <div className="space-y-3">
            {c.phase_details.map((phase: string, i: number) => (
              <div key={i} className="rounded-xl border border-neutral-700 bg-neutral-800/50 p-3">
                <Prose text={phase} />
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Stack Choices */}
      {c.stack_choices?.length > 0 && (
        <Section title="Stack Choices">
          <ul className="space-y-2">
            {c.stack_choices.map((choice: string, i: number) => (
              <li key={i} className="flex gap-2 text-xs text-neutral-400">
                <span className="text-blue-500 shrink-0">›</span>{choice}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Risks */}
      {c.risks?.length > 0 && (
        <Section title="Risks">
          <div className="space-y-3">
            {c.risks.map((r: any, i: number) => (
              <div key={i} className="rounded-xl border border-neutral-700 bg-neutral-800/50 p-3 space-y-1">
                <p className="text-sm text-white">{r.risk}</p>
                <p className="text-xs text-yellow-400">Likelihood: {r.likelihood}</p>
                <p className="text-xs text-neutral-400">{r.mitigation}</p>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Next Steps */}
      {c.next_steps?.length > 0 && (
        <Section title="Next Steps">
          <ul className="space-y-2">
            {c.next_steps.map((step: string, i: number) => (
              <li key={i} className="text-sm text-neutral-400">{step}</li>
            ))}
          </ul>
        </Section>
      )}

      {/* Long-form prose sections */}
      {sections.map(({ key, label }) =>
        c[key] ? (
          <Section key={key} title={label}>
            <Prose text={c[key]} />
          </Section>
        ) : null
      )}
    </div>
  );
}

/* ── Selections Tab ──────────────────────────────────────────────────────── */

function SelectionsTab({ scan, useCases, solutions }: { scan: any; useCases: any[]; solutions: any[] }) {
  const selectedUcIds: string[] = scan?.selected_use_case_ids ?? [];
  const selectedSolId: string   = scan?.selected_solution_id ?? "";

  const selectedUcs  = (useCases ?? []).filter((uc: any) => selectedUcIds.includes(uc.id));
  const selectedSol  = (solutions ?? []).find((s: any) => s.id === selectedSolId);

  return (
    <div className="space-y-4">
      <Section title="Selected Use Cases">
        {selectedUcs.length === 0 ? (
          <p className="text-sm text-neutral-500">None selected.</p>
        ) : (
          <div className="space-y-2">
            {selectedUcs.map((uc: any, i: number) => (
              <div key={i} className="flex items-center gap-3 rounded-xl border border-neutral-700 bg-neutral-800/50 p-3">
                <Badge value={`${Math.round((uc.confidence_score ?? 0) * 100)}%`} color="blue" />
                <span className="text-sm text-white">{uc.title}</span>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="Selected Solution">
        {!selectedSol ? (
          <p className="text-sm text-neutral-500">None selected.</p>
        ) : (
          <div className="rounded-xl border border-neutral-700 bg-neutral-800/50 p-3 space-y-1">
            <p className="text-sm text-white font-medium">{selectedSol.title}</p>
            <p className="text-xs text-neutral-400">{selectedSol.pitch}</p>
            <div className="flex gap-2 mt-2">
              <Badge value={`Value: ${selectedSol.value_score}`} color="green" />
              <Badge value={`Effort: ${selectedSol.effort_score}`} color="yellow" />
              <Badge value={selectedSol.timeline} color="neutral" />
            </div>
          </div>
        )}
      </Section>
    </div>
  );
}

/* ── Pipeline Log Tab ────────────────────────────────────────────────────── */

function LogTab({ log }: { log: any[] }) {
  if (!log?.length) return <p className="text-neutral-500">No pipeline log entries.</p>;
  return (
    <div className="rounded-2xl border border-neutral-800 bg-neutral-900 overflow-hidden">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-neutral-500 border-b border-neutral-800">
            <th className="px-4 py-3 font-medium">Stage</th>
            <th className="px-4 py-3 font-medium">Message</th>
            <th className="px-4 py-3 font-medium hidden sm:table-cell">Timestamp</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-800">
          {log.map((entry: any, i: number) => (
            <tr key={i} className="hover:bg-neutral-800/40 transition">
              <td className="px-4 py-2.5 text-blue-400 font-mono">{entry.stage ?? entry.node ?? "—"}</td>
              <td className="px-4 py-2.5 text-neutral-400">{entry.message ?? JSON.stringify(entry)}</td>
              <td className="px-4 py-2.5 text-neutral-600 hidden sm:table-cell">
                {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
