"use client";

import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  Award,
  CheckCircle2,
  Clock,
  IndianRupee,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import type { RecoveryWorkflowResponse } from "@/types/ripple";

interface RecoveryPlansViewProps {
  workflow: RecoveryWorkflowResponse | null;
  onApprove: (optionId: string, decision: "APPROVE" | "REJECT") => void;
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

export function RecoveryPlansView({
  workflow,
  onApprove,
  onTriggerDemo,
  actionLoading,
}: RecoveryPlansViewProps) {
  const [selectedId, setSelectedId] = useState<string>("");

  useEffect(() => {
    if (workflow?.selected_option_id) {
      setSelectedId(workflow.selected_option_id);
    } else if (workflow?.recommended_option_id) {
      setSelectedId(workflow.recommended_option_id);
    }
  }, [workflow?.selected_option_id, workflow?.recommended_option_id]);

  if (!workflow || workflow.recovery_options.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-800 bg-[#0B1324] p-12 text-center">
        <Award className="h-10 w-10 text-sky-400" />
        <h2 className="mt-4 text-lg font-semibold text-white">
          No Recovery Options Generated Yet
        </h2>
        <p className="mt-2 max-w-md text-sm text-slate-400">
          Trigger a disruption first to let Google OR-Tools optimize replacement
          routes, costs, and deadline compliance.
        </p>
        <button
          onClick={onTriggerDemo}
          disabled={actionLoading}
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-sky-500 px-5 py-2.5 text-sm font-semibold text-slate-950 hover:bg-sky-400 disabled:opacity-60"
        >
          <AlertTriangle className="h-4 w-4" />
          Trigger Demo Disruption
        </button>
      </div>
    );
  }

  const options = workflow.recovery_options;
  const maxFare = Math.max(...options.map((o) => o.additional_cost_inr), 1);
  const isPending = workflow.approval_status === "PENDING";
  const isExecuted = workflow.approval_status === "EXECUTED";
  const isRejected = workflow.approval_status === "REJECTED";
  const activeOption =
    options.find((o) => o.id === selectedId) ?? options[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Recovery Plans & Human Approval
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Ranked by Google OR-Tools CP-SAT across arrival deadline (08:45
            IST), cost, stops, and corporate policy.
          </p>
        </div>
        <StatusBadge label={workflow.approval_status} />
      </div>

      {/* Cost & Arrival Comparison Chart */}
      <div className="grid gap-6 lg:grid-cols-12">
        <div className="rounded-2xl border border-slate-800 bg-[#0B1324] p-5 lg:col-span-6">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-white">
            <IndianRupee className="h-4 w-4 text-sky-400" />
            Fare vs Policy Cap Comparison (₹18,000 limit)
          </h2>
          <div className="mt-4 space-y-3">
            {options.map((opt) => {
              const pct = Math.min(
                100,
                Math.round((opt.additional_cost_inr / maxFare) * 100)
              );
              return (
                <div key={opt.id} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="truncate font-medium text-slate-200">
                      {opt.carrier_codes.join(" + ")} ·{" "}
                      {opt.stops === 0 ? "Non-stop" : `${opt.stops} stop`}
                    </span>
                    <span className="font-semibold text-white">
                      ₹{opt.additional_cost_inr.toLocaleString("en-IN")}
                    </span>
                  </div>
                  <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-800">
                    <div
                      style={{ width: `${pct}%` }}
                      className={`h-full rounded-full ${
                        opt.is_recommended
                          ? "bg-sky-400"
                          : opt.is_policy_compliant
                            ? "bg-slate-400"
                            : "bg-rose-500"
                      }`}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-[#0B1324] p-5 lg:col-span-6">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-white">
            <Clock className="h-4 w-4 text-sky-400" />
            Arrival vs 09:30 AM Client Meeting Deadline
          </h2>
          <div className="mt-4 space-y-2.5">
            {options.map((opt) => (
              <div
                key={opt.id}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/50 px-3.5 py-2.5 text-xs"
              >
                <div>
                  <div className="font-medium text-white">
                    {opt.carrier_codes.join(" + ")}
                  </div>
                  <div className="text-slate-400">
                    Arrives {formatTime(opt.arrival_time)} IST
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                      opt.meets_deadline
                        ? "bg-emerald-500/15 text-emerald-300"
                        : "bg-rose-500/15 text-rose-300"
                    }`}
                  >
                    {opt.meets_deadline ? "Meets 08:45 Buffer" : "Misses Meeting"}
                  </span>
                  <span className="rounded bg-slate-800 px-2 py-0.5 font-semibold text-sky-300">
                    Score {opt.optimizer_score}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Candidate Recovery Option Cards */}
      <div className="grid gap-4 lg:grid-cols-2">
        {options.map((opt) => {
          const isSelected = activeOption.id === opt.id;
          return (
            <div
              key={opt.id}
              onClick={() => isPending && setSelectedId(opt.id)}
              className={`rounded-2xl border p-5 transition ${
                isPending ? "cursor-pointer" : ""
              } ${
                isSelected
                  ? "border-sky-500 bg-sky-500/10 shadow-lg shadow-sky-500/10"
                  : "border-slate-800 bg-[#0B1324] hover:border-slate-700"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-[11px] font-bold text-slate-200">
                      Rank #{opt.rank}
                    </span>
                    {opt.is_recommended && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-sky-500/20 px-2.5 py-0.5 text-[11px] font-semibold text-sky-300">
                        <Award className="h-3 w-3" /> OR-Tools Recommended
                      </span>
                    )}
                    <span className="rounded bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold text-amber-300">
                      {opt.inventory_mode}
                    </span>
                  </div>
                  <h3 className="mt-2 text-base font-semibold text-white">
                    {opt.label}
                  </h3>
                  <p className="mt-0.5 text-xs text-slate-400">
                    {opt.route_description} · Dep{" "}
                    {formatTime(opt.departure_time)} → Arr{" "}
                    {formatTime(opt.arrival_time)}
                  </p>
                </div>

                <div className="text-right">
                  <div className="text-lg font-bold text-white">
                    ₹{opt.additional_cost_inr.toLocaleString("en-IN")}
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Net ₹{opt.net_cost_after_refund_inr.toLocaleString("en-IN")}
                  </div>
                </div>
              </div>

              {/* Feasibility Flags */}
              <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
                <span
                  className={`rounded-full px-2.5 py-0.5 font-medium ${
                    opt.preserves_meeting
                      ? "bg-emerald-500/15 text-emerald-300"
                      : "bg-rose-500/15 text-rose-300"
                  }`}
                >
                  {opt.preserves_meeting
                    ? "Preserves 09:30 Meeting"
                    : "Misses 09:30 Meeting"}
                </span>
                <span
                  className={`rounded-full px-2.5 py-0.5 font-medium ${
                    opt.is_policy_compliant
                      ? "bg-emerald-500/15 text-emerald-300"
                      : "bg-rose-500/15 text-rose-300"
                  }`}
                >
                  {opt.is_policy_compliant
                    ? "Policy Compliant"
                    : "Policy Violation"}
                </span>
                <span
                  className={`rounded-full px-2.5 py-0.5 font-medium ${
                    opt.preserves_hotel_checkin
                      ? "bg-emerald-500/15 text-emerald-300"
                      : "bg-amber-500/15 text-amber-300"
                  }`}
                >
                  {opt.preserves_hotel_checkin
                    ? "Hotel Hold Intact"
                    : "Hotel Hold Notification Needed"}
                </span>
              </div>

              <ul className="mt-3 space-y-1 text-xs text-slate-300">
                {opt.constraint_notes.map((note, idx) => (
                  <li key={idx}>• {note}</li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      {/* Human-in-the-Loop Approval Checkpoint */}
      <div className="rounded-2xl border border-amber-500/30 bg-[#0B1324] p-6">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm font-semibold text-amber-300">
              <ShieldAlert className="h-4 w-4" />
              Human-in-the-Loop Approval Checkpoint
            </div>
            <p className="text-xs text-slate-300">
              Selected Plan:{" "}
              <span className="font-semibold text-white">
                {activeOption.label}
              </span>{" "}
              ({activeOption.actions.length} coordinated actions across airline,
              transfer, and hotel providers). RIPPLE never purchases or modifies
              bookings without your explicit authorization.
            </p>
          </div>

          {isPending && (
            <div className="flex shrink-0 flex-wrap gap-3">
              <button
                onClick={() => onApprove(activeOption.id, "REJECT")}
                disabled={actionLoading}
                className="inline-flex items-center gap-1.5 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-xs font-semibold text-rose-200 transition hover:bg-rose-500/20 disabled:opacity-60"
              >
                <XCircle className="h-4 w-4" />
                Reject Plan
              </button>
              <button
                onClick={() => onApprove(activeOption.id, "APPROVE")}
                disabled={actionLoading}
                className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-500 px-5 py-2 text-xs font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:opacity-60"
              >
                <CheckCircle2 className="h-4 w-4" />
                {actionLoading ? "Executing..." : "Approve & Execute Plan"}
              </button>
            </div>
          )}
        </div>

        {/* Planned Action Steps */}
        <div className="mt-4 grid gap-2.5 md:grid-cols-2">
          {activeOption.actions.map((step) => (
            <div
              key={step.step_order}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-xs"
            >
              <div className="flex items-center justify-between font-semibold text-white">
                <span>
                  Step {step.step_order}: {step.action_type.replaceAll("_", " ")}
                </span>
                <span className="text-sky-300">{step.provider}</span>
              </div>
              <p className="mt-1 text-slate-300">{step.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Post-Approval Execution & Verification Panel */}
      {isExecuted && (
        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-base font-semibold text-emerald-300">
              <ShieldCheck className="h-5 w-5" />
              Execution & Verification Complete
            </div>
            <StatusBadge
              label={workflow.verification_passed ? "VERIFIED" : "FAILED"}
            />
          </div>
          <p className="mt-1.5 text-sm text-slate-200">
            {workflow.verification_summary}
          </p>

          <div className="mt-4 space-y-2">
            {workflow.execution_logs.map((log) => (
              <div
                key={`${log.step_order}-${log.confirmation_code}`}
                className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-emerald-500/20 bg-slate-900/70 px-4 py-3 text-xs"
              >
                <div>
                  <span className="font-semibold text-white">
                    {log.step_order}. {log.action_type}
                  </span>{" "}
                  <span className="text-slate-400">({log.provider})</span>
                  <p className="mt-0.5 text-slate-300">{log.message}</p>
                </div>
                <div className="flex items-center gap-2">
                  <code className="rounded bg-slate-800 px-2 py-0.5 text-sky-300">
                    {log.confirmation_code}
                  </code>
                  <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-amber-300">
                    {log.adapter_mode}
                  </span>
                  <StatusBadge label={log.status} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {isRejected && (
        <div className="rounded-2xl border border-rose-500/30 bg-rose-950/20 p-5 text-sm text-rose-200">
          Human reviewer rejected the recovery plan. No bookings were modified.
          Use <span className="font-semibold">Reset Baseline Trip</span> or
          re-run the disruption simulation to evaluate again.
        </div>
      )}
    </div>
  );
}
