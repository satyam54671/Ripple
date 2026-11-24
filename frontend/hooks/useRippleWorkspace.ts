"use client";

import { useCallback, useEffect, useState } from "react";
import { rippleApi } from "@/services/api";
import type {
  HealthStatus,
  MCPToolsResponse,
  RecoveryWorkflowResponse,
  TripItinerary,
} from "@/types/ripple";

export type RippleTab =
  | "dashboard"
  | "trip-details"
  | "disruption-analysis"
  | "recovery-plans";

export function useRippleWorkspace() {
  const [activeTab, setActiveTab] = useState<RippleTab>("dashboard");
  const [trips, setTrips] = useState<TripItinerary[]>([]);
  const [selectedTripId, setSelectedTripId] = useState<string>(
    "trip_blr_bom_del_001"
  );
  const [workflow, setWorkflow] = useState<RecoveryWorkflowResponse | null>(
    null
  );
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [mcpTools, setMcpTools] = useState<MCPToolsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const refreshAll = useCallback(
    async (tripIdToLoad?: string) => {
      try {
        setError(null);
        const [healthRes, tripsRes, toolsRes] = await Promise.all([
          rippleApi.getHealth(),
          rippleApi.getTrips(),
          rippleApi.getMcpTools(),
        ]);
        setHealth(healthRes);
        setTrips(tripsRes);
        setMcpTools(toolsRes);

        const targetId =
          tripIdToLoad ||
          (tripsRes.some((t) => t.id === selectedTripId)
            ? selectedTripId
            : tripsRes[0]?.id);

        if (targetId) {
          setSelectedTripId(targetId);
          const wfRes = await rippleApi.getTripWorkflow(targetId);
          setWorkflow(wfRes);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to connect to RIPPLE backend API"
        );
      } finally {
        setLoading(false);
      }
    },
    [selectedTripId]
  );

  useEffect(() => {
    void refreshAll("trip_blr_bom_del_001");
  }, [refreshAll]);

  const selectTrip = useCallback(async (tripId: string) => {
    setSelectedTripId(tripId);
    setError(null);
    try {
      const wf = await rippleApi.getTripWorkflow(tripId);
      setWorkflow(wf);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workflow");
    }
  }, []);

  const triggerDemoCancellation = useCallback(async () => {
    setActionLoading(true);
    setError(null);
    try {
      const wf = await rippleApi.triggerDemoCancellation();
      setSelectedTripId("trip_blr_bom_del_001");
      setWorkflow(wf);
      const updatedTrips = await rippleApi.getTrips();
      setTrips(updatedTrips);
      setActiveTab("disruption-analysis");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to trigger demo disruption"
      );
    } finally {
      setActionLoading(false);
    }
  }, []);

  const resetDemo = useCallback(async () => {
    setActionLoading(true);
    setError(null);
    try {
      await rippleApi.resetDemo();
      setWorkflow(null);
      setSelectedTripId("trip_blr_bom_del_001");
      const updatedTrips = await rippleApi.getTrips();
      setTrips(updatedTrips);
      setActiveTab("dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset demo");
    } finally {
      setActionLoading(false);
    }
  }, []);

  const submitApproval = useCallback(
    async (optionId: string, decision: "APPROVE" | "REJECT") => {
      if (!workflow) return;
      setActionLoading(true);
      setError(null);
      try {
        const updatedWf = await rippleApi.approveWorkflow(
          workflow.run_id,
          optionId,
          decision
        );
        setWorkflow(updatedWf);
        const updatedTrips = await rippleApi.getTrips();
        setTrips(updatedTrips);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to submit decision"
        );
      } finally {
        setActionLoading(false);
      }
    },
    [workflow]
  );

  const selectedTrip =
    trips.find((t) => t.id === selectedTripId) ?? trips[0] ?? null;

  return {
    activeTab,
    setActiveTab,
    trips,
    selectedTrip,
    selectedTripId,
    selectTrip,
    workflow,
    health,
    mcpTools,
    loading,
    actionLoading,
    error,
    refreshAll,
    triggerDemoCancellation,
    resetDemo,
    submitApproval,
  };
}
