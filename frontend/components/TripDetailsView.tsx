"use client";

import React from "react";
import {
  ArrowRight,
  Building2,
  Car,
  Plane,
  ShieldCheck,
  Users,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import type { NodeType, TripItinerary, TripNode } from "@/types/ripple";

interface TripDetailsViewProps {
  trip: TripItinerary | null;
}

function getNodeIcon(type: NodeType) {
  switch (type) {
    case "FLIGHT":
      return Plane;
    case "HOTEL":
      return Building2;
    case "TRANSFER":
      return Car;
    case "MEETING":
      return Users;
  }
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function TripDetailsView({ trip }: TripDetailsViewProps) {
  if (!trip) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-[#0B1324] p-8 text-center text-sm text-slate-400">
        No trip selected.
      </div>
    );
  }

  const nodeMap = new Map<string, TripNode>(trip.nodes.map((n) => [n.id, n]));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              {trip.title}
            </h1>
            <StatusBadge label={trip.status} />
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Traveller: <span className="text-slate-200">{trip.traveller_name}</span>{" "}
            ({trip.traveller_email}) · Corridor:{" "}
            <span className="font-medium text-sky-300">
              {trip.origin} → {trip.destination}
            </span>
          </p>
        </div>

        {/* Travel Policy Pill */}
        <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-[#0B1324] px-4 py-2.5 text-xs">
          <ShieldCheck className="h-4 w-4 text-sky-400" />
          <div>
            <div className="font-semibold text-white">Company Policy</div>
            <div className="text-slate-400">
              Max ₹{trip.policy.max_rebooking_budget_inr.toLocaleString("en-IN")} ·{" "}
              {trip.policy.preferred_cabin} · {trip.policy.min_meeting_buffer_minutes}m
              meeting buffer
            </div>
          </div>
        </div>
      </div>

      {/* Visual Trip Dependency Graph */}
      <div className="rounded-2xl border border-slate-800 bg-[#0B1324] p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold text-white">
              Trip Dependency Graph (DAG)
            </h2>
            <p className="text-xs text-slate-400">
              Directed temporal dependencies & minimum buffer constraints used to
              trace cascade failures.
            </p>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-rose-400" /> Hard Dependency
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-sky-400" /> Soft / Advisable
            </span>
          </div>
        </div>

        {/* Ordered Node Flow */}
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          {trip.nodes.map((node, index) => {
            const Icon = getNodeIcon(node.node_type);
            const isBroken =
              node.status === "CANCELLED" || node.status === "MISSED_CONNECTION";
            const isAtRisk = node.status === "AT_RISK";
            const borderColor = isBroken
              ? "border-rose-500/50 bg-rose-500/10"
              : isAtRisk
                ? "border-amber-500/50 bg-amber-500/10"
                : node.status === "REBOOKED" || node.status === "RESCHEDULED"
                  ? "border-sky-500/50 bg-sky-500/10"
                  : "border-slate-700/80 bg-slate-900/70";

            return (
              <div
                key={node.id}
                className={`relative flex flex-col justify-between rounded-xl border p-4 ${borderColor}`}
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-sky-300">
                      <Icon className="h-3.5 w-3.5" />
                      {index + 1}. {node.node_type}
                    </span>
                    <StatusBadge label={node.status} />
                  </div>
                  <h3 className="mt-2.5 text-sm font-semibold text-white">
                    {node.title}
                  </h3>
                  <p className="mt-1 text-xs text-slate-400">{node.location}</p>
                </div>

                <div className="mt-4 border-t border-slate-800/80 pt-2.5 text-[11px] text-slate-300">
                  <div>Start: {formatDateTime(node.start_time)}</div>
                  <div className="text-slate-400">
                    Ref: {node.booking_reference} · Priority: {node.priority}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Dependency Edges Table */}
        <div className="mt-5 grid gap-2.5 md:grid-cols-2">
          {trip.edges.map((edge, idx) => {
            const src = nodeMap.get(edge.source_node_id);
            const tgt = nodeMap.get(edge.target_node_id);
            return (
              <div
                key={`${edge.source_node_id}-${edge.target_node_id}-${idx}`}
                className="flex items-start justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-3 text-xs"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-1.5 font-medium text-white">
                    <span>{src?.title ?? edge.source_node_id}</span>
                    <ArrowRight className="h-3.5 w-3.5 text-sky-400" />
                    <span>{tgt?.title ?? edge.target_node_id}</span>
                  </div>
                  <p className="mt-1 text-slate-400">{edge.description}</p>
                </div>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                    edge.is_hard_dependency
                      ? "bg-rose-500/15 text-rose-300"
                      : "bg-sky-500/15 text-sky-300"
                  }`}
                >
                  {edge.is_hard_dependency ? "HARD" : "SOFT"} · {edge.min_buffer_minutes}m
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detailed Booking Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        {trip.nodes.map((node) => {
          const Icon = getNodeIcon(node.node_type);
          return (
            <div
              key={node.id}
              className="rounded-2xl border border-slate-800 bg-[#0B1324] p-5"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-800 text-sky-400">
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">
                      {node.title}
                    </h3>
                    <p className="text-xs text-slate-400">
                      {node.provider} · Ref {node.booking_reference}
                    </p>
                  </div>
                </div>
                <StatusBadge label={node.status} />
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 rounded-xl bg-slate-900/60 p-3 text-xs">
                <div>
                  <div className="text-slate-400">Window</div>
                  <div className="mt-0.5 font-medium text-slate-200">
                    {formatDateTime(node.start_time)} →{" "}
                    {formatDateTime(node.end_time)}
                  </div>
                </div>
                <div>
                  <div className="text-slate-400">Priority & Cost</div>
                  <div className="mt-0.5 font-medium text-slate-200">
                    {node.priority} ·{" "}
                    {node.cost_inr > 0
                      ? `₹${node.cost_inr.toLocaleString("en-IN")}`
                      : "Calendar Event"}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
