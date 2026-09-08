/**
 * Lightweight event tracker.
 * Fires-and-forgets a POST to /api/events — never blocks the UI.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function useTrack(scanId: string | null, userId?: string | null) {
  return function track(eventType: string, metadata?: Record<string, unknown>) {
    if (!scanId) return;
    fetch(`${API_URL}/api/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scan_id: scanId,
        event_type: eventType,
        user_id: userId ?? null,
        metadata: metadata ?? {},
      }),
    }).catch(() => {});
  };
}
