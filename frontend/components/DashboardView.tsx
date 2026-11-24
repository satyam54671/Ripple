"use client";

import React from "react";
import {
  AlertTriangle,
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  Plane,
  ShieldAlert,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import type { RippleTab } from "@/hooks/useRippleWorkspace";
import type { RecoveryWorkflowResponse, TripItinerary } from "@/types/ripple";

interface DashboardViewProps {
  trips: TripItinerary[];
  selectedTrip: TripItinerary | null;
  workflow: RecoveryWorkflowResponse | null;
  onSelectTrip: (tripId: string) => void;
  onNavigate: (tab: RippleTab) => void;
  onTriggerDemo: () => void;
  actionLoading: boolean;
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function DashboardView({
  trips,
  selectedTrip,
  workflow,
  onSelectTrip,
  onNavigate,
  onTriggerDemo,
  actionLoading,
}: DashboardViewProps) {
  const disruptedCount = trips.filter(
    (t) => t.status === "DISRUPTED" || t.status === "AWAITING_APPROVAL"
  ).length;
  const recoveredCount = trips.filter((t) => t.status === "RECOVERED").length;
  const pendingApproval = workflow?.approval_status === "PENDING" ? 1 : 0;
  const allNodes = selectedTrip?.nodes ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Travel Operations Dashboard
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Real-time itinerary monitoring, dependency graph tracing, and
            human-approved disruption recovery.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {workflow ? (
            <button
              onClick={() => onNavigate("recovery-plans")}
              className="inline-flex items-center gap-2 rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400"
            >
              Review Recovery Plan
              <ArrowRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              onClick={onTriggerDemo}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 disabled:opacity-60"
            >
              <AlertTriangle className="h-4 w-4" />
              {actionLoading ? "Simulating..." : "Run Demo Disruption"}
            </button>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-[#0B1324] p-5">
          <div className="flex items-center justify-between text-xs font-medium text-slate-400">
            <span>Monitored Trips</span>
            <Plane className="h-4 w-4 text-sky-400" />
          </div>
          <div className="mt-3 text-3xl font-bold text-white">{trips.length}</div>
          <p className="mt-1 text-xs text-slate-400">
            Unified flights, hotels, transfers & meetings
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-[#0B1324] p-5">
          <div className="flex items-center justify-between text-xs font-medium text-slate-400">
            <span>Active Disruptions</span>
            <AlertTriangle className="h-4 w-4 text-rose-400" />
          </div>
          <div className="mt-3 text-3xl font-bold text-white">
            {disruptedCount}
          </div>
          <p className="mt-1 text-xs text-slate-400">
            {disruptedCount > 0
              ? "Cascade impact traced across downstream nodes"
              : "All active flights currently on schedule"}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-[#0B1324] p-5">
          <div className="flex items-center justify-between text-xs font-medium text-slate-400">
            <span>Pending Human Approval</span>
            <ShieldAlert className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-3 text-3xl font-bold text-white">
            {pendingApproval}
          </div>
          <p className="mt-1 text-xs text-slate-400">
            No bookings modified without explicit sign-off
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-[#0B1324] p-5">
          <div className="flex items-center justify-between text-xs font-medium text-slate-400">
            <span>Recovered Trips</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-3 text-3xl font-bold text-white">
            {recoveredCount}
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Verified via MCP post-execution checks
          </p>
        </div>
      </div>

      {/* Main Content Split */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Monitored Trips */}
        <div className="space-y-4 rounded-2xl border border-slate-800 bg-[#0B1324] p-5 lg:col-span-7">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white">
              Active Corporate Trips
            </h2>
            <span className="text-xs text-slate-400">
              Click a trip to inspect dependencies
            </span>
          </div>

          <div className="space-y-3">
            {trips.map((trip) => {
              const isSelected = trip.id === selectedTrip?.id;
              return (
                <div
                  key={trip.id}
                  onClick={() => onSelectTrip(trip.id)}
                  className={`cursor-pointer rounded-xl border p-4 transition ${
                    isSelected
                      ? "border-sky-500/50 bg-sky-500/10"
                      : "border-slate-800 bg-slate-900/50 hover:border-slate-700"
                  }`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">
                          {trip.title}
                        </span>
                        <StatusBadge label={trip.status} />
                      </div>
                      <p className="mt-1 text-xs text-slate-400">
                        Traveller:{" "}
                        <span className="text-slate-200">
                          {trip.traveller_name}
                        </span>{" "}
                        · Route:{" "}
                        <span className="text-sky-300">
                          {trip.origin} → {trip.destination}
                        </span>{" "}
                        · {trip.nodes.length} linked commitments
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectTrip(trip.id);
                        onNavigate("trip-details");
                      }}
                      className="rounded-lg border border-slate-700 bg-slate-800/80 px-2.5 py-1 text-xs font-medium text-slate-200 hover:bg-slate-700"
                    >
                      Inspect Graph
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Recovery Pipeline Status */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                LangGraph Recovery Status
              </span>
              {workflow && <StatusBadge label={workflow.current_stage} />}
            </div>
            {workflow ? (
              <div className="space-y-2 text-xs text-slate-300">
                <p>
                  <span className="text-slate-400">Run ID:</span>{" "}
                  <code className="text-sky-300">{workflow.run_id}</code> ·{" "}
                  <span className="text-slate-400">Approval:</span>{" "}
                  <span className="font-semibold text-white">
                    {workflow.approval_status}
                  </span>
                </p>
                {workflow.impact_analysis && (
                  <p className="text-slate-300">
                    {workflow.impact_analysis.summary}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-400">
                No active disruption workflow for this trip. Use{" "}
                <span className="text-sky-300">Trigger BLR→BOM Cancellation</span>{" "}
                in the sidebar to launch the multi-agent recovery pipeline.
              </p>
            )}
          </div>
        </div>

        {/* Upcoming Commitments */}
        <div className="space-y-4 rounded-2xl border border-slate-800 bg-[#0B1324] p-5 lg:col-span-5">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-base font-semibold text-white">
              <CalendarClock className="h-4 w-4 text-sky-400" />
              Upcoming Commitments
            </h2>
            <span className="text-xs text-slate-400">
              {selectedTrip?.origin} → {selectedTrip?.destination}
            </span>
          </div>

          <div className="space-y-2.5">
            {allNodes.map((node) => (
              <div
                key={node.id}
                className="flex items-start justify-between gap-3 rounded-xl border border-slate-800/80 bg-slate-900/50 p-3.5"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-semibold text-sky-300">
                      {node.node_type}
                    </span>
                    <span className="truncate text-sm font-medium text-white">
                      {node.title}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-400">
                    {formatTime(node.start_time)} · {node.provider} (
                    {node.booking_reference})
                  </p>
                </div>
                <StatusBadge label={node.status} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
