import React from "react";

const STATUS_STYLES: Record<string, string> = {
  ON_TRACK: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  CONFIRMED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  ON_TIME: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  RECOVERED: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  REBOOKED: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  RESCHEDULED: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  VERIFIED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  EXECUTED: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  COMPLETED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  AWAITING_APPROVAL: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  WAITING_APPROVAL: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  PENDING: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  AT_RISK: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  NEEDS_UPDATE: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  DELAYED: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  DISRUPTED: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  CANCELLED: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  MISSED_CONNECTION: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  BROKEN: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  ROOT_CAUSE: "bg-rose-500/20 text-rose-200 border-rose-500/40",
  REJECTED: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  UNAFFECTED: "bg-slate-700/40 text-slate-300 border-slate-600/40",
};

export function StatusBadge({ label }: { label: string }) {
  const style =
    STATUS_STYLES[label] ?? "bg-slate-700/40 text-slate-200 border-slate-600/40";
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-medium tracking-wide ${style}`}
    >
      {label.replaceAll("_", " ")}
    </span>
  );
}
