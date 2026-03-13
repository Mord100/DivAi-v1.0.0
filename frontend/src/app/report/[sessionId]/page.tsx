"use client";

import { use, useEffect, useRef, useState } from "react";
import Link from "next/link";
import clsx from "clsx";
import { Container } from "@/components/Container";
import { FadeIn, FadeInStagger } from "@/components/FadeIn";
import {
  ReportResponse, UseCase, SolutionCard, ProposalContent, EffortRow, RiskItem,
} from "@/types/divai";
import { useProposalChat } from "@/hooks/useProposalChat";
import { ArrowLeft, ArrowUp, Download, Loader2, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Tab = "intelligence" | "use_cases" | "solutions" | "proposal";

// ── Shared primitives ─────────────────────────────────────────────────────────

function Pill({ children, accent }: { children: React.ReactNode; accent?: boolean }) {
  return (
    <span className={clsx(
      "inline-flex rounded-full px-3 py-1 text-xs font-medium",
      accent ? "bg-blue-600 text-white" : "bg-neutral-100 text-neutral-600"
    )}>
      {children}
    </span>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 rounded-full bg-neutral-100">
        <div className="h-full rounded-full bg-blue-600" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold text-blue-600 w-8">{pct}%</span>
    </div>
  );
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-neutral-400">
      {children}
    </h3>
  );
}

// ── Intelligence tab ──────────────────────────────────────────────────────────

function IntelligenceTab({ report }: { report: ReportResponse["intelligence_report"] }) {
  if (!report) return null;
  const ts = report.tech_stack ?? {};
  return (
    <div className="space-y-10">
      <FadeIn>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { label: "Category", value: report.business_category },
            { label: "Frontend", value: ts.frontend_framework },
            { label: "Language", value: ts.language },
            { label: "Auth",     value: report.auth_pattern?.method },
          ].map((item) => (
            <div key={item.label} className="rounded-2xl border border-neutral-200 p-4">
              <p className="text-xs text-neutral-400 mb-1">{item.label}</p>
              <p className="font-semibold text-neutral-950 truncate">{item.value ?? "—"}</p>
            </div>
          ))}
        </div>
      </FadeIn>
      <FadeIn>
        <SectionHeading>Key features</SectionHeading>
        <div className="flex flex-wrap gap-2">
          {report.key_features.map((f) => <Pill key={f}>{f}</Pill>)}
        </div>
      </FadeIn>
      {report.api_endpoints?.length > 0 && (
        <FadeIn>
          <SectionHeading>API endpoints ({report.api_endpoints.length})</SectionHeading>
          <div className="divide-y divide-neutral-100 rounded-2xl border border-neutral-200 overflow-hidden">
            {report.api_endpoints.map((ep, i) => (
              <div key={i} className="flex items-center gap-4 px-5 py-3">
                <span className="w-14 shrink-0 rounded-md bg-neutral-950 px-2 py-0.5 text-center text-xs font-bold text-white">
                  {ep.method}
                </span>
                <code className="flex-1 min-w-0 text-sm font-mono text-neutral-700 truncate">{ep.url_pattern}</code>
                <span className="text-xs text-neutral-400 hidden sm:block truncate max-w-xs">{ep.inferred_purpose}</span>
              </div>
            ))}
          </div>
        </FadeIn>
      )}
      {report.integrations?.length > 0 && (
        <FadeIn>
          <SectionHeading>Integrations</SectionHeading>
          <div className="flex flex-wrap gap-2">
            {report.integrations.map((i) => <Pill key={i} accent>{i}</Pill>)}
          </div>
        </FadeIn>
      )}
      {report.analyst_notes && (
        <FadeIn>
          <SectionHeading>Analyst notes</SectionHeading>
          <p className="text-sm text-neutral-600 leading-relaxed">{report.analyst_notes}</p>
        </FadeIn>
      )}
    </div>
  );
}

// ── Use cases tab ─────────────────────────────────────────────────────────────

function UseCasesTab({ useCases }: { useCases: UseCase[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const effortColour: Record<string, string> = {
    Low: "text-green-700 bg-green-50", Medium: "text-yellow-700 bg-yellow-50", High: "text-red-700 bg-red-50",
  };
  return (
    <FadeInStagger faster>
      <div className="space-y-4">
        {useCases.map((uc) => (
          <FadeIn key={uc.id}>
            <div className="rounded-2xl border border-neutral-200 overflow-hidden">
              <button
                onClick={() => setExpanded(expanded === uc.id ? null : uc.id)}
                className="w-full text-left p-5 hover:bg-neutral-50 transition"
              >
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-4 mb-2">
                      <p className="font-semibold text-neutral-950">{uc.title}</p>
                      <div className="flex items-center gap-2 shrink-0">
                        {uc.effort_estimate && (
                          <span className={clsx("rounded-full px-2.5 py-0.5 text-xs font-medium", effortColour[uc.effort_estimate] ?? "text-neutral-500 bg-neutral-100")}>
                            {uc.effort_estimate}
                          </span>
                        )}
                        {expanded === uc.id ? <ChevronUp className="h-4 w-4 text-neutral-400" /> : <ChevronDown className="h-4 w-4 text-neutral-400" />}
                      </div>
                    </div>
                    <ConfidenceBar value={uc.confidence_score} />
                  </div>
                </div>
              </button>
              {expanded === uc.id && (
                <div className="border-t border-neutral-100 px-5 pb-5 pt-4">
                  <p className="text-sm text-neutral-600 leading-relaxed mb-4">{uc.description}</p>
                  {uc.tags?.length > 0 && <div className="flex flex-wrap gap-1.5 mb-4">{uc.tags.map((t) => <Pill key={t}>{t}</Pill>)}</div>}
                  {uc.supporting_evidence?.length > 0 && (
                    <div>
                      <p className="text-xs font-medium uppercase tracking-widest text-neutral-400 mb-2">Evidence</p>
                      <ul className="space-y-1.5">
                        {uc.supporting_evidence.map((ev, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-neutral-500">
                            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400" />{ev}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </FadeIn>
        ))}
      </div>
    </FadeInStagger>
  );
}

// ── Solutions tab ─────────────────────────────────────────────────────────────

function SolutionsTab({ solutions }: { solutions: SolutionCard[] }) {
  const [expanded, setExpanded] = useState<string | null>(solutions[0]?.id ?? null);
  const effortColour: Record<string, string> = {
    Low: "text-green-700 bg-green-50", Medium: "text-yellow-700 bg-yellow-50", High: "text-red-700 bg-red-50",
  };
  return (
    <FadeInStagger faster>
      <div className="space-y-4">
        {solutions.map((sol) => (
          <FadeIn key={sol.id}>
            <div className="rounded-2xl border border-neutral-200 overflow-hidden">
              <button
                onClick={() => setExpanded(expanded === sol.id ? null : sol.id)}
                className="w-full text-left p-5 hover:bg-neutral-50 transition"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="font-semibold text-neutral-950">{sol.title}</p>
                    <p className="text-sm text-neutral-500 italic mt-0.5">{sol.pitch}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={clsx("rounded-full px-2.5 py-0.5 text-xs font-medium", effortColour[sol.effort_score] ?? "text-neutral-500 bg-neutral-100")}>{sol.effort_score}</span>
                    <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">{sol.value_score}</span>
                    {expanded === sol.id ? <ChevronUp className="h-4 w-4 text-neutral-400" /> : <ChevronDown className="h-4 w-4 text-neutral-400" />}
                  </div>
                </div>
              </button>
              {expanded === sol.id && (
                <div className="border-t border-neutral-100 px-5 pb-5 pt-4 space-y-6">
                  <p className="text-sm text-neutral-600 leading-relaxed">{sol.architecture_overview}</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <div>
                      <SectionHeading>Stack</SectionHeading>
                      <div className="flex flex-wrap gap-1.5">{sol.stack.map((s) => <Pill key={s}>{s}</Pill>)}</div>
                    </div>
                    <div>
                      <SectionHeading>Phases — {sol.timeline}</SectionHeading>
                      <ul className="space-y-1.5">
                        {sol.phases.map((p, i) => (
                          <li key={i} className="text-sm text-neutral-600 flex items-start gap-2">
                            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-neutral-300" />{p}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </FadeIn>
        ))}
      </div>
    </FadeInStagger>
  );
}

// ── Proposal section wrapper ──────────────────────────────────────────────────

function ProposalSection({
  title, children, updated = false,
}: {
  title: string; children: React.ReactNode; updated?: boolean;
}) {
  return (
    <section className={clsx(
      "rounded-2xl border p-6 transition-all duration-700",
      updated ? "border-blue-400 ring-2 ring-blue-400/20" : "border-neutral-200"
    )}>
      <h3 className="text-sm font-semibold uppercase tracking-widest text-neutral-400 mb-4">{title}</h3>
      {children}
    </section>
  );
}

// ── Chat panel ────────────────────────────────────────────────────────────────

function ChatPanel({
  sessionId, proposalContent, onSectionUpdate,
}: {
  sessionId: string;
  proposalContent: ProposalContent | undefined;
  onSectionUpdate: (section: string, content: string) => void;
}) {
  const { messages, isStreaming, sendMessage } = useProposalChat(
    sessionId, proposalContent, onSectionUpdate
  );
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSubmit() {
    if (!input.trim() || isStreaming) return;
    sendMessage(input);
    setInput("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="flex flex-col h-full rounded-2xl border border-neutral-200 bg-white overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-neutral-100">
        <p className="text-xs font-semibold uppercase tracking-widest text-neutral-400">
          Proposal chat
        </p>
        <p className="text-xs text-neutral-400 mt-0.5">
          Ask questions or request edits — changes apply live
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="space-y-2 pt-2">
            {[
              "Make the executive summary more concise",
              "What's the estimated delivery timeline?",
              "Add more detail to the security section",
              "Rewrite the problem statement for a technical audience",
            ].map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => sendMessage(suggestion)}
                className="w-full text-left text-xs text-neutral-400 hover:text-neutral-700 hover:bg-neutral-50 rounded-lg px-3 py-2 transition-colors duration-150"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={clsx("flex", msg.role === "user" ? "justify-end" : "justify-start")}>
            {msg.role === "user" ? (
              <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-neutral-950 px-3.5 py-2.5 text-sm text-white">
                {msg.content}
              </div>
            ) : (
              <div className="max-w-[92%] text-sm text-neutral-700 leading-relaxed whitespace-pre-wrap">
                {msg.content}
                {msg.streaming && (
                  <span className="inline-block w-0.5 h-3.5 bg-neutral-400 ml-0.5 animate-pulse" />
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-neutral-100 px-4 py-3 flex items-end gap-2">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question or request an edit…"
          rows={1}
          disabled={isStreaming}
          className="flex-1 resize-none rounded-xl border border-neutral-200 bg-neutral-50 px-3 py-2.5 text-sm text-neutral-950 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-950/10 focus:border-neutral-400 disabled:opacity-50 transition-colors leading-relaxed"
          style={{ maxHeight: "120px", overflowY: "auto" }}
        />
        <button
          onClick={handleSubmit}
          disabled={!input.trim() || isStreaming}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-neutral-950 text-white hover:bg-neutral-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          {isStreaming
            ? <Loader2 className="h-4 w-4 animate-spin" />
            : <ArrowUp className="h-4 w-4" />
          }
        </button>
      </div>
    </div>
  );
}

// ── Proposal tab ──────────────────────────────────────────────────────────────

function ProposalTab({
  paths, content, updatedSections, sessionId, onSectionUpdate,
}: {
  paths: ReportResponse["proposal_paths"];
  content: ProposalContent | undefined;
  updatedSections: Set<string>;
  sessionId: string;
  onSectionUpdate: (section: string, newContent: string) => void;
}) {
  if (!paths) return <p className="text-neutral-400">No proposal generated.</p>;

  return (
    // Two-column layout: proposal preview (3/5) + chat panel (2/5)
    <div className="grid grid-cols-1 xl:grid-cols-5 gap-8 items-start">

      {/* ── Left: proposal preview ── */}
      <div className="xl:col-span-3 space-y-6">
        {/* Header card */}
        <FadeIn>
          <div className="rounded-2xl border border-neutral-200 p-8">
            <p className="text-xs font-medium uppercase tracking-widest text-neutral-400 mb-2">Proposal document</p>
            <h2 className="text-2xl font-semibold text-neutral-950 mb-1">{paths.title}</h2>
            <p className="text-neutral-500">Prepared for {paths.client}</p>
            <div className="mt-6 flex flex-wrap gap-3">
              <a
                href={`${API_URL}/api/download/${sessionId}`}
                download
                className="inline-flex items-center gap-2 rounded-full bg-neutral-950 px-5 py-2 text-sm font-semibold text-white hover:bg-neutral-800 transition"
              >
                <Download className="h-4 w-4" /> Download .docx
              </a>
              {paths.pdf && (
                <a href={paths.pdf} download className="inline-flex items-center gap-2 rounded-full border border-neutral-300 px-5 py-2 text-sm font-semibold text-neutral-950 hover:bg-neutral-50 transition">
                  <Download className="h-4 w-4" /> PDF
                </a>
              )}
              {paths.notion && (
                <a href={paths.notion} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-full border border-neutral-300 px-5 py-2 text-sm font-semibold text-neutral-950 hover:bg-neutral-50 transition">
                  <ExternalLink className="h-4 w-4" /> Notion
                </a>
              )}
            </div>
          </div>
        </FadeIn>

        {content && (
          <>
            {content.executive_summary && (
              <FadeIn>
                <ProposalSection title="Executive Summary" updated={updatedSections.has("executive_summary")}>
                  <p className="text-sm text-neutral-600 leading-relaxed">{content.executive_summary}</p>
                </ProposalSection>
              </FadeIn>
            )}
            {content.problem_statement && (
              <FadeIn>
                <ProposalSection title="Problem Statement" updated={updatedSections.has("problem_statement")}>
                  <p className="text-sm text-neutral-600 leading-relaxed">{content.problem_statement}</p>
                </ProposalSection>
              </FadeIn>
            )}
            {content.proposed_architecture && (
              <FadeIn>
                <ProposalSection title="Proposed Architecture" updated={updatedSections.has("proposed_architecture")}>
                  <p className="text-sm text-neutral-600 leading-relaxed">{content.proposed_architecture}</p>
                </ProposalSection>
              </FadeIn>
            )}
            {content.stack_choices?.length > 0 && (
              <FadeIn>
                <ProposalSection title="Technology Stack">
                  <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {content.stack_choices.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-neutral-600">
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400" />{s}
                      </li>
                    ))}
                  </ul>
                </ProposalSection>
              </FadeIn>
            )}
            {content.phase_details?.length > 0 && (
              <FadeIn>
                <ProposalSection title="Delivery Phases">
                  <div className="space-y-3">
                    {content.phase_details.map((p, i) => (
                      <div key={i} className="flex gap-4">
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-neutral-950 text-xs font-bold text-white">{i + 1}</span>
                        <p className="text-sm text-neutral-600 leading-relaxed pt-0.5">{p}</p>
                      </div>
                    ))}
                  </div>
                </ProposalSection>
              </FadeIn>
            )}
            {content.api_specifications && (
              <FadeIn>
                <ProposalSection title="API Specifications" updated={updatedSections.has("api_specifications")}>
                  <p className="text-sm text-neutral-600 leading-relaxed">{content.api_specifications}</p>
                </ProposalSection>
              </FadeIn>
            )}
            {content.security_compliance && (
              <FadeIn>
                <ProposalSection title="Security & Compliance" updated={updatedSections.has("security_compliance")}>
                  <p className="text-sm text-neutral-600 leading-relaxed">{content.security_compliance}</p>
                </ProposalSection>
              </FadeIn>
            )}
            {content.testing_strategy && (
              <FadeIn>
                <ProposalSection title="Testing Strategy" updated={updatedSections.has("testing_strategy")}>
                  <p className="text-sm text-neutral-600 leading-relaxed">{content.testing_strategy}</p>
                </ProposalSection>
              </FadeIn>
            )}
            {content.deployment_devops && (
              <FadeIn>
                <ProposalSection title="Deployment & DevOps" updated={updatedSections.has("deployment_devops")}>
                  <p className="text-sm text-neutral-600 leading-relaxed">{content.deployment_devops}</p>
                </ProposalSection>
              </FadeIn>
            )}
            {content.effort_rows?.length > 0 && (
              <FadeIn>
                <ProposalSection title="Effort Estimate">
                  <div className="overflow-x-auto rounded-xl border border-neutral-200">
                    <table className="w-full text-sm">
                      <thead className="bg-neutral-50 border-b border-neutral-200">
                        <tr>{["Phase", "Weeks", "Team", "Cost Range"].map((h) => (
                          <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wide">{h}</th>
                        ))}</tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-100">
                        {content.effort_rows.map((row: EffortRow, i: number) => (
                          <tr key={i} className="hover:bg-neutral-50 transition">
                            <td className="px-4 py-3 font-medium text-neutral-950">{row.phase}</td>
                            <td className="px-4 py-3 text-neutral-600">{row.weeks}</td>
                            <td className="px-4 py-3 text-neutral-600">{row.team}</td>
                            <td className="px-4 py-3 text-neutral-600">{row.cost_range}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </ProposalSection>
              </FadeIn>
            )}
            {content.investment_summary && (
              <FadeIn>
                <ProposalSection title="Investment Summary" updated={updatedSections.has("investment_summary")}>
                  <p className="text-sm text-neutral-600 leading-relaxed">{content.investment_summary}</p>
                </ProposalSection>
              </FadeIn>
            )}
            {content.risks?.length > 0 && (
              <FadeIn>
                <ProposalSection title="Risks & Mitigations">
                  <div className="space-y-3">
                    {content.risks.map((r: RiskItem, i: number) => (
                      <div key={i} className="rounded-xl border border-neutral-200 p-4">
                        <div className="flex items-start justify-between gap-4">
                          <p className="text-sm font-medium text-neutral-950">{r.risk}</p>
                          <span className={clsx("shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium",
                            r.likelihood === "High" ? "bg-red-50 text-red-700" :
                            r.likelihood === "Medium" ? "bg-yellow-50 text-yellow-700" : "bg-green-50 text-green-700"
                          )}>{r.likelihood}</span>
                        </div>
                        <p className="mt-1.5 text-xs text-neutral-500">{r.mitigation}</p>
                      </div>
                    ))}
                  </div>
                </ProposalSection>
              </FadeIn>
            )}
            {content.next_steps?.length > 0 && (
              <FadeIn>
                <ProposalSection title="Next Steps">
                  <ol className="space-y-2">
                    {content.next_steps.map((step: string, i: number) => (
                      <li key={i} className="flex items-start gap-3 text-sm text-neutral-600">
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">{i + 1}</span>
                        {step}
                      </li>
                    ))}
                  </ol>
                </ProposalSection>
              </FadeIn>
            )}
          </>
        )}
      </div>

      {/* ── Right: chat panel (sticky) ── */}
      <div className="xl:col-span-2 xl:sticky xl:top-24" style={{ height: "calc(100vh - 8rem)" }}>
        <ChatPanel
          sessionId={sessionId}
          proposalContent={content}
          onSectionUpdate={onSectionUpdate}
        />
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

interface PageProps { params: Promise<{ sessionId: string }> }

export default function ReportPage({ params }: PageProps) {
  const { sessionId } = use(params);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("intelligence");

  // Live proposal content state — starts from pipeline output, updated by chat edits
  const [proposalContent, setProposalContent] = useState<ProposalContent | undefined>();
  // Tracks recently-updated sections for the flash highlight
  const [updatedSections, setUpdatedSections] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetch(`${API_URL}/api/report/${sessionId}`)
      .then((r) => r.json())
      .then((data: ReportResponse) => {
        setReport(data);
        // Initialise live content from pipeline output
        if (data.proposal_paths?.content) {
          setProposalContent(data.proposal_paths.content as ProposalContent);
        }
        setLoading(false);
      });
  }, [sessionId]);

  // Called by the chat hook when Claude edits a section
  function handleSectionUpdate(section: string, newContent: string) {
    setProposalContent((prev) => prev ? { ...prev, [section]: newContent } : prev);
    // Flash the updated section, then clear after 2.5s
    setUpdatedSections((prev) => new Set([...prev, section]));
    setTimeout(() => {
      setUpdatedSections((prev) => {
        const next = new Set(prev);
        next.delete(section);
        return next;
      });
    }, 2500);
    // Auto-switch to proposal tab if not already there
    setActiveTab("proposal");
  }

  const tabs: Array<{ id: Tab; label: string; count?: number }> = [
    { id: "intelligence", label: "Intelligence" },
    { id: "use_cases",    label: "Use Cases",  count: report?.use_cases?.length },
    { id: "solutions",    label: "Solutions",  count: report?.solutions?.length },
    { id: "proposal",     label: "Proposal" },
  ];

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-neutral-100 bg-white sticky top-0 z-10">
        <Container>
          <div className="flex h-16 items-center gap-4">
            <Link href={`/scan/${sessionId}`} className="flex items-center gap-1.5 text-sm font-medium text-neutral-400 hover:text-neutral-950 transition">
              <ArrowLeft className="h-4 w-4" /> Back
            </Link>
            <div className="h-4 w-px bg-neutral-200" />
            <span className="font-display text-lg font-medium text-neutral-950 truncate">
              {loading ? "Loading…" : report?.intelligence_report?.target_url ?? "Report"}
            </span>
          </div>
        </Container>
      </header>

      {loading ? (
        <Container className="py-32 flex items-center justify-center">
          <div className="flex items-center gap-3 text-neutral-400">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Loading report…</span>
          </div>
        </Container>
      ) : !report || report.status === "error" ? (
        <Container className="py-16">
          <FadeIn>
            <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
              <p className="font-semibold text-red-900">Error</p>
              <p className="mt-1 text-sm text-red-700">{report?.error ?? "Failed to load"}</p>
            </div>
          </FadeIn>
        </Container>
      ) : (
        // Proposal tab needs full width; other tabs are contained
        <div className={clsx(activeTab === "proposal" ? "px-6 xl:px-10" : "")}>
          <Container className={clsx(activeTab === "proposal" ? "max-w-none" : "")}>
            <FadeIn>
              <div className="py-10 pb-0">
                <p className="text-xs font-medium uppercase tracking-widest text-neutral-400 mb-2">Intelligence report</p>
                <h1 className="font-display text-3xl font-medium tracking-tight text-neutral-950 sm:text-4xl">
                  {report.intelligence_report?.business_category ?? "Analysis complete"}
                </h1>
              </div>
            </FadeIn>

            <FadeIn>
              <div className="flex gap-0 border-b border-neutral-200 mt-8 mb-10 overflow-x-auto">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={clsx(
                      "flex items-center gap-1.5 px-5 py-3.5 text-sm font-medium whitespace-nowrap border-b-2 -mb-px transition",
                      activeTab === tab.id
                        ? "border-neutral-950 text-neutral-950"
                        : "border-transparent text-neutral-400 hover:text-neutral-700"
                    )}
                  >
                    {tab.label}
                    {tab.count !== undefined && (
                      <span className="rounded-full bg-neutral-100 px-1.5 py-0.5 text-xs text-neutral-500">{tab.count}</span>
                    )}
                  </button>
                ))}
              </div>
            </FadeIn>

            <div className="pb-16">
              {activeTab === "intelligence" && <IntelligenceTab report={report.intelligence_report} />}
              {activeTab === "use_cases"    && report.use_cases && <UseCasesTab useCases={report.use_cases} />}
              {activeTab === "solutions"    && report.solutions && <SolutionsTab solutions={report.solutions} />}
              {activeTab === "proposal"     && (
                <ProposalTab
                  paths={report.proposal_paths}
                  content={proposalContent}
                  updatedSections={updatedSections}
                  sessionId={sessionId}
                  onSectionUpdate={handleSectionUpdate}
                />
              )}
            </div>
          </Container>
        </div>
      )}
    </div>
  );
}
