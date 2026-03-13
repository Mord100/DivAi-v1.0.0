"use client";

import { useEffect, useState, useRef } from "react";
import {
  PipelineEvent, NodeState, PIPELINE_NODES,
  UseCase, SolutionCard, InteractionType,
} from "@/types/divai";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface PendingInteraction {
  type: InteractionType;
  use_cases?: UseCase[];
  solutions?: SolutionCard[];
  message?: string;
}

interface UseAgentStreamResult {
  events: PipelineEvent[];
  nodes: NodeState[];
  isConnected: boolean;
  isComplete: boolean;
  error: string | null;
  currentNode: string | null;
  pendingInteraction: PendingInteraction | null;
  submitInteraction: (payload: {
    selected_use_case_ids?: string[];
    selected_solution_id?: string;
  }) => Promise<void>;
}

export function useAgentStream(sessionId: string | null): UseAgentStreamResult {
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [nodes, setNodes] = useState<NodeState[]>(
    PIPELINE_NODES.map((n) => ({ ...n, status: "pending" }))
  );
  const [isConnected, setIsConnected] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentNode, setCurrentNode] = useState<string | null>(null);
  const [pendingInteraction, setPendingInteraction] = useState<PendingInteraction | null>(null);
  const runningNodeRef = useRef<string | null>(null);

  async function submitInteraction(payload: {
    selected_use_case_ids?: string[];
    selected_solution_id?: string;
  }) {
    if (!sessionId) return;

    // Optimistically mark the next node as running immediately so there
    // is no gap between the user submitting and the backend resuming.
    // "selected_use_case_ids" means we just finished use_case → next is solution
    // "selected_solution_id"   means we just finished solution  → next is proposal
    const nextNode = payload.selected_use_case_ids !== undefined ? "solution" : "proposal";
    setNodes((prev) => prev.map((n) =>
      n.name === nextNode ? { ...n, status: "running" } : n
    ));
    setCurrentNode(nextNode);
    runningNodeRef.current = nextNode;

    setPendingInteraction(null);

    await fetch(`${API_URL}/api/interact/${sessionId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  useEffect(() => {
    if (!sessionId) return;
    const es = new EventSource(`${API_URL}/api/stream/${sessionId}`);
    setIsConnected(true);

    es.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data) as PipelineEvent;
      setEvents((prev) => [...prev, data]);

      if (data.type === "pipeline_start") {
        runningNodeRef.current = "ingestion";
        setCurrentNode("ingestion");
        setNodes((prev) => prev.map((n) =>
          n.name === "ingestion" ? { ...n, status: "running" } : n
        ));
      }

      if (data.type === "node_complete" && data.node) {
        const completed = data.node;
        const idx = PIPELINE_NODES.findIndex((n) => n.name === completed);
        const next = PIPELINE_NODES[idx + 1];
        setNodes((prev) => prev.map((n) => {
          if (n.name === completed)
            return { ...n, status: data.data?.error ? "error" : "complete", data: data.data, completedAt: data.timestamp };
          // Only auto-advance to "running" if there's no pending interaction expected
          // (the interaction_required event will handle it otherwise)
          if (next && n.name === next.name && n.status !== "running")
            return { ...n, status: "running" };
          return n;
        }));
        if (next) { runningNodeRef.current = next.name; setCurrentNode(next.name); }
      }

      if (data.type === "interaction_required") {
        // Keep currentNode as-is — the last completed node's "running" sibling
        // was already set, and we want the UI to show "awaiting" rather than blank.
        const interactionData = (data as PipelineEvent & { data?: { use_cases?: UseCase[]; solutions?: SolutionCard[]; message?: string } }).data;
        setPendingInteraction({
          type: data.interaction_type!,
          use_cases: interactionData?.use_cases,
          solutions: interactionData?.solutions,
          message: interactionData?.message,
        });
        // Reset the "next" node back to pending — it hasn't started yet
        const nextNodeName = data.interaction_type === "select_use_cases" ? "solution" : "proposal";
        setCurrentNode(null);
        setNodes((prev) => prev.map((n) =>
          n.name === nextNodeName ? { ...n, status: "pending" } : n
        ));
      }

      if (data.type === "pipeline_complete") {
        setIsComplete(true);
        setCurrentNode(null);
        setPendingInteraction(null);
        es.close();
        setIsConnected(false);
      }

      if (data.type === "stream_end") { es.close(); setIsConnected(false); }

      if (data.type === "error") {
        setError(data.message ?? "Pipeline error");
        if (runningNodeRef.current) {
          setNodes((prev) => prev.map((n) =>
            n.name === runningNodeRef.current ? { ...n, status: "error" } : n
          ));
        }
        setPendingInteraction(null);
        es.close();
        setIsConnected(false);
      }
    };

    es.onerror = () => { setIsConnected(false); es.close(); };
    return () => { es.close(); setIsConnected(false); };
  }, [sessionId]);

  return { events, nodes, isConnected, isComplete, error, currentNode, pendingInteraction, submitInteraction };
}
