"use client";

import { useState, useRef } from "react";
import { ProposalContent } from "@/types/divai";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

/**
 * useProposalChat — manages the proposal chat session.
 *
 * CONCEPT: Fetch Streaming (not EventSource)
 * -------------------------------------------
 * EventSource only supports GET requests. For chat we need POST (to send
 * the message body). So we use fetch() with a ReadableStream reader instead.
 *
 * The response is a text/event-stream but we read it manually:
 *   const reader = response.body.getReader()
 *   while (true) { const { done, value } = await reader.read(); ... }
 *
 * We decode SSE lines ourselves: any line starting with "data: " is a JSON event.
 *
 * CONCEPT: current_content as Live Context
 * -----------------------------------------
 * Each request sends the current proposalContent state to the backend.
 * This means if the user made edits earlier in the session (section_update events),
 * Claude sees those edits — not just the original pipeline output.
 * The frontend is the source of truth for the live proposal state.
 */
export function useProposalChat(
  sessionId: string,
  proposalContent: ProposalContent | undefined,
  onSectionUpdate: (section: string, content: string) => void
) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  // historyRef accumulates the conversation for multi-turn context
  const historyRef = useRef<Array<{ role: string; content: string }>>([]);

  async function sendMessage(text: string) {
    if (isStreaming || !text.trim()) return;

    const trimmed = text.trim();
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    // Snapshot history before state update
    const history = historyRef.current.slice();

    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);

    const assistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "", streaming: true },
    ]);

    let assistantText = "";

    try {
      const response = await fetch(`${API_URL}/api/chat/${sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          history,
          // Send live content so Claude works from the latest edited version
          current_content: proposalContent ?? null,
        }),
      });

      if (!response.ok) {
        const err = await response.text();
        throw new Error(err || `HTTP ${response.status}`);
      }

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        // SSE lines end with \n; split and keep any incomplete line in buffer
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));

            if (event.type === "delta" && event.text) {
              assistantText += event.text;
              const snapshot = assistantText;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: snapshot } : m
                )
              );
            }

            if (event.type === "section_update" && event.section && event.content) {
              onSectionUpdate(event.section, event.content);
            }

            if (event.type === "error") {
              assistantText += `\n\n_Error: ${event.message}_`;
              const snapshot = assistantText;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: snapshot } : m
                )
              );
            }
          } catch {
            // Malformed SSE line — skip
          }
        }
      }

      // Add completed exchange to history for next turn
      historyRef.current = [
        ...history,
        { role: "user", content: trimmed },
        { role: "assistant", content: assistantText },
      ];
    } catch (err) {
      const errText = err instanceof Error ? err.message : "Unknown error";
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: `_Could not reach the server: ${errText}_` }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, streaming: false } : m
        )
      );
    }
  }

  return { messages, isStreaming, sendMessage };
}
