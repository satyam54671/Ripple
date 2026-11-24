"use client";

import React from "react";
import {
  AlertTriangle,
  ArrowRight,
  Clock,
  Cpu,
  GitMerge,
  ShieldCheck,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import type { RippleTab } from "@/hooks/useRippleWorkspace";
import type { RecoveryWorkflowResponse } from "@/types/ripple";

interface DisruptionAnalysisViewProps {
  workflow: RecoveryWorkflowResponse | null;
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

export function DisruptionAnalysisView({
  workflow,
  onNavigate,
  onTriggerDemo,
  actionLoading,
}: DisruptionAnalysisViewProps) {
  if (!workflow || !workflow.disruption || !workflow.impact_analysis) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-800 bg-[#0B1324] p-12 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-500/15 text-sky-400">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h2 className="mt-4 text-lg font-semibold text-white">
          No Active Disruption Detected
        </h2>
        <p className="mt-2 max-w-md text-sm text-slate-400">
          Trigger the BLR → BOM → DEL demo cancellation to watch RIPPLE verify
          the disruption via MCP and trace cascade impact across connecting
          flights, transfer, hotel, and the 09:30 AM client meeting.
        </p>
        <button
          onClick={onTriggerDemo}
          disabled={actionLoading}
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-sky-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 disabled:opacity-60"
        >
          <AlertTriangle className="h-4 w-4" />
          {actionLoading ? "Running Analysis..." : "Simulate Flight 6E-512 Cancellation"}
        </button>
      </div>
    );
  }

  const { disruption, impact_analysis: impact } = workflow;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Disruption & Cascade Impact Analysis
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Verified via MCP telemetry and traced through the Trip Dependency
            Graph.
          </p>
        </div>
        <button
          onClick={() => onNavigate("recovery-plans")}
          className="inline-flex items-center gap-2 rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400"
        >
          View OR-Tools Recovery Plans
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* Disruption Event Alert Card */}
      <div className="rounded-2xl border border-rose-500/30 bg-rose-950/20 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-500/20 text-rose-300">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base font-semibold text-white">
                  {disruption.disruption_type} Verified on Node{" "}
                  <code className="text-rose-200">{disruption.node_id}</code>
                </h2>
                <StatusBadge label={disruption.severity} />
                {disruption.verified && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-medium text-emerald-300">
                    <ShieldCheck className="h-3 w-3" /> MCP Telemetry Verified
                  </span>
                )}
              </div>
              <p className="mt-1.5 text-sm text-slate-200">
                {disruption.reason}
              </p>
              <p className="mt-1 text-xs text-slate-400">
                Source: {disruption.source} · Affected Downstream Nodes:{" "}
                <span className="font-semibold text-white">
                  {impact.total_affected}
                </span>
              </p>
            </div>
          </div>
          <StatusBadge label={workflow.current_stage} />
        </div>
      </div>

      {/* Main Grid: Impact Timeline + LangGraph Trace */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Cascade Impact Timeline */}
        <div className="space-y-4 rounded-2xl border border-slate-800 bg-[#0B1324] p-5 lg:col-span-7">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-base font-semibold text-white">
              <Clock className="h-4 w-4 text-sky-400" />
              Affected Commitments Timeline
            </h2>
            <span className="text-xs text-slate-400">
              {impact.total_affected} downstream commitment(s) impacted
            </span>
          </div>

          <div className="relative space-y-3 pl-4 before:absolute before:bottom-3 before:left-1.5 before:top-3 before:w-px before:bg-slate-800">
            {impact.impacted_nodes.map((node) => (
              <div
                key={node.node_id}
                className="relative rounded-xl border border-slate-800 bg-slate-900/60 p-4"
              >
                <span
                  className={`absolute -left-[15px] top-5 h-2.5 w-2.5 rounded-full ring-4 ring-[#0B1324] ${
                    node.impact_level === "ROOT_CAUSE" ||
                    node.impact_level === "BROKEN"
                      ? "bg-rose-400"
                      : node.impact_level === "AT_RISK" ||
                          node.impact_level === "NEEDS_UPDATE"
                        ? "bg-amber-400"
                        : "bg-emerald-400"
                  }`}
                />
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-semibold text-sky-300">
                        {node.node_type}
                      </span>
                      <span className="text-sm font-semibold text-white">
                        {node.title}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-400">
                      Scheduled: {formatTime(node.original_start)} →{" "}
                      {formatTime(node.original_end)}
                    </p>
                  </div>
                  <StatusBadge label={node.impact_level} />
                </div>

                <p className="mt-2.5 text-xs text-slate-300">{node.reason}</p>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-800/80 pt-2.5 text-[11px]">
                  <span className="text-sky-300">
                    Action: {node.recommended_action}
                  </span>
                  <span className="flex items-center gap-1 text-slate-400">
                    <GitMerge className="h-3 w-3" />
                    {node.dependency_path.join(" → ")}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* LangGraph Agent Execution Trace */}
        <div className="space-y-4 rounded-2xl border border-slate-800 bg-[#0B1324] p-5 lg:col-span-5">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-base font-semibold text-white">
              <Cpu className="h-4 w-4 text-sky-400" />
              LangGraph Multi-Agent Trace
            </h2>
            <span className="text-xs text-slate-400">Stateful Pipeline</span>
          </div>

          <div className="space-y-2.5">
            {workflow.workflow_trace.map((entry, idx) => (
              <div
                key={`${entry.stage}-${idx}`}
                className="rounded-xl border border-slate-800 bg-slate-900/50 p-3.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-white">
                    {idx + 1}. {entry.stage.replaceAll("_", " ")}
                  </span>
                  <StatusBadge label={entry.status} />
                </div>
                <div className="mt-1 text-[11px] font-medium text-sky-300">
                  {entry.agent}
                </div>
                <p className="mt-1 text-xs leading-relaxed text-slate-300">
                  {entry.message}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
