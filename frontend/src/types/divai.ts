// DivAi Frontend Types — mirrors src/state/divai_state.py + src/api/models.py

export type EventType =
  | "pipeline_start"
  | "node_complete"
  | "interaction_required"
  | "pipeline_complete"
  | "error"
  | "heartbeat"
  | "stream_end";

export type InteractionType = "select_use_cases" | "select_solution";

export interface PipelineEvent {
  type: EventType;
  node?: string;
  label?: string;
  stage?: string;
  data?: NodeData;
  message?: string;
  url?: string;
  depth?: string;
  proposal_title?: string;
  timestamp: string;
  // interaction_required fields
  interaction_type?: InteractionType;
}

export interface NodeData {
  current_stage?: string;
  error?: string;
  scrape_summary?: {
    url: string;
    dom_chars: number;
    request_count: number;
    tech_detected: string[];
  };
  report_summary?: {
    business_category: string;
    key_features_count: number;
    endpoints_count: number;
    tech_stack: Record<string, string>;
    key_features: string[];
    integrations: string[];
    analyst_notes: string;
  };
  use_cases_count?: number;
  use_case_titles?: Array<{ title: string; confidence: number }>;
  solutions_count?: number;
  solution_titles?: Array<{ title: string; timeline: string }>;
  proposal?: { title: string; client: string; docx_path: string };
}

// ── API shapes ───────────────────────────────────────────────────────────────

export interface ScanRequest { url: string; depth?: "surface" | "deep" }
export interface ScanResponse {
  session_id: string; message: string;
  stream_url: string; status_url: string; report_url: string;
}

// ── Pipeline node UI state ───────────────────────────────────────────────────

export type NodeStatus = "pending" | "running" | "complete" | "error";
export interface NodeState {
  name: string; label: string;
  status: NodeStatus; data?: NodeData; completedAt?: string;
}

export const PIPELINE_NODES: Array<{ name: string; label: string }> = [
  { name: "ingestion",    label: "Scraping website" },
  { name: "analysis",     label: "Analysing business signals" },
  { name: "human_review", label: "Intelligence report ready" },
  { name: "use_case",     label: "Generating use cases" },
  { name: "solution",     label: "Designing solutions" },
  { name: "proposal",     label: "Writing proposal" },
];

// ── Full pipeline data (from GET /api/report) ────────────────────────────────

export interface TechStack {
  frontend_framework?: string; language?: string; hosting_signals?: string[];
  database_signals?: string[]; confidence?: number;
}
export interface ApiEndpoint { method: string; url_pattern: string; inferred_purpose: string }
export interface IntelligenceReport {
  target_url: string; business_category: string;
  tech_stack: TechStack; key_features: string[];
  api_endpoints: ApiEndpoint[]; data_models: string[];
  integrations: string[];
  auth_pattern: { method: string; providers: string[]; token_refresh: boolean; notes: string };
  analyst_notes: string;
}

export interface UseCase {
  id: string; title: string; description: string;
  confidence_score: number; supporting_evidence: string[];
  tags: string[]; effort_estimate: string;
}

export interface SolutionCard {
  id: string; title: string; pitch: string;
  architecture_overview: string; stack: string[];
  phases: string[]; timeline: string;
  effort_score: "Low" | "Medium" | "High";
  value_score: string; risks: string[]; prerequisites: string[];
  addresses_use_case: string;
}

export interface EffortRow { phase: string; weeks: string; team: string; cost_range: string }
export interface RiskItem { risk: string; likelihood: string; mitigation: string }

export interface ProposalContent {
  client_name: string; project_title: string; prepared_by: string;
  executive_summary: string; problem_statement: string;
  proposed_architecture: string; stack_choices: string[];
  phase_details: string[]; api_specifications: string;
  security_compliance: string; testing_strategy: string;
  deployment_devops: string; effort_rows: EffortRow[];
  investment_summary: string; risks: RiskItem[]; next_steps: string[];
}

export interface ProposalPaths {
  docx: string; pdf: string | null; notion: string | null;
  title: string; client: string;
  content?: ProposalContent;
}

export interface ReportResponse {
  session_id: string; status: string;
  intelligence_report?: IntelligenceReport;
  use_cases?: UseCase[]; solutions?: SolutionCard[];
  proposal_paths?: ProposalPaths;
  pipeline_log?: Array<{ stage: string; message: string; timestamp: string }>;
  error?: string;
}
