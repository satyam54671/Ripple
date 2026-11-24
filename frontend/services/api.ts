import type {
  HealthStatus,
  MCPToolsResponse,
  RecoveryWorkflowResponse,
  TripItinerary,
} from "@/types/ripple";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Request failed");
    throw new Error(`API ${response.status}: ${errorText}`);
  }

  return response.json() as Promise<T>;
}

export const rippleApi = {
  getHealth: () => request<HealthStatus>("/health"),
  getTrips: () => request<TripItinerary[]>("/trips"),
  getTrip: (tripId: string) => request<TripItinerary>(`/trips/${tripId}`),
  getTripWorkflow: (tripId: string) =>
    request<RecoveryWorkflowResponse | null>(`/trips/${tripId}/workflow`),
  triggerDemoCancellation: () =>
    request<RecoveryWorkflowResponse>("/demo/trigger-cancellation", {
      method: "POST",
    }),
  resetDemo: () =>
    request<TripItinerary>("/demo/reset", {
      method: "POST",
    }),
  approveWorkflow: (
    runId: string,
    optionId: string,
    decision: "APPROVE" | "REJECT",
    reviewerNote = ""
  ) =>
    request<RecoveryWorkflowResponse>(`/workflows/${runId}/approve`, {
      method: "POST",
      body: JSON.stringify({
        option_id: optionId,
        decision,
        reviewer_note: reviewerNote,
      }),
    }),
  getMcpTools: () => request<MCPToolsResponse>("/mcp/tools"),
};
