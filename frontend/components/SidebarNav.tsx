"use client";

import React from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  GitBranch,
  LayoutDashboard,
  Plane,
  RotateCcw,
  ShieldCheck,
  Zap,
} from "lucide-react";
import type { RippleTab } from "@/hooks/useRippleWorkspace";
import type { HealthStatus, MCPToolsResponse } from "@/types/ripple";

interface SidebarNavProps {
  activeTab: RippleTab;
  onSelectTab: (tab: RippleTab) => void;
  onTriggerDemo: () => void;
  onResetDemo: () => void;
  actionLoading: boolean;
  health: HealthStatus | null;
  mcpTools: MCPToolsResponse | null;
  hasActiveWorkflow: boolean;
}

const NAV_ITEMS: Array<{
  id: RippleTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}> = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "trip-details", label: "Trip Details & Graph", icon: GitBranch },
  { id: "disruption-analysis", label: "Disruption Analysis", icon: AlertTriangle },
  { id: "recovery-plans", label: "Recovery Plans", icon: CheckCircle2 },
];

export function SidebarNav({
  activeTab,
  onSelectTab,
  onTriggerDemo,
  onResetDemo,
  actionLoading,
  health,
  mcpTools,
  hasActiveWorkflow,
}: SidebarNavProps) {
  return (
    <aside className="flex w-full flex-col justify-between border-b border-slate-800/80 bg-[#080F1F] p-5 lg:min-h-screen lg:w-72 lg:border-b-0 lg:border-r">
      <div className="space-y-6">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-blue-600 shadow-lg shadow-sky-500/20">
            <Plane className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-white">
                RIPPLE
              </span>
              <span className="rounded bg-sky-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-sky-300">
                v0.1
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Disruption Recovery Engine
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="space-y-1.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-sm font-medium transition ${
                  isActive
                    ? "bg-sky-500/15 text-sky-300 ring-1 ring-sky-500/30"
                    : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
                }`}
              >
                <span className="flex items-center gap-2.5">
                  <Icon className="h-4 w-4" />
                  {item.label}
                </span>
                {item.id === "disruption-analysis" && hasActiveWorkflow && (
                  <span className="h-2 w-2 rounded-full bg-amber-400" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Demo Scenario Runner */}
        <div className="rounded-2xl border border-sky-500/20 bg-slate-900/70 p-4">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-sky-300">
            <Zap className="h-3.5 w-3.5" />
            Hackathon Demo
          </div>
          <p className="mb-3 text-xs leading-relaxed text-slate-400">
            Simulate IndiGo <span className="text-slate-200">6E-512</span>{" "}
            cancellation on <span className="text-slate-200">BLR → BOM → DEL</span>{" "}
            impacting the 09:30 AM client meeting.
          </p>
          <div className="space-y-2">
            <button
              onClick={onTriggerDemo}
              disabled={actionLoading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-sky-500 px-3 py-2 text-xs font-semibold text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              {actionLoading ? "Running Workflow..." : "Trigger BLR→BOM Cancellation"}
            </button>
            <button
              onClick={onResetDemo}
              disabled={actionLoading}
              className="flex w-full items-center justify-center gap-1.5 rounded-xl border border-slate-700 bg-slate-800/60 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-slate-800 hover:text-white disabled:opacity-60"
            >
              <RotateCcw className="h-3 w-3" />
              Reset Baseline Trip
            </button>
          </div>
        </div>
      </div>

      {/* System Telemetry Footer */}
      <div className="mt-6 space-y-2.5 border-t border-slate-800/80 pt-4 text-xs text-slate-400">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5 text-emerald-400" />
            FastAPI + LangGraph
          </span>
          <span className="font-medium text-emerald-300">
            {health ? "Online" : "Offline"}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-sky-400" />
            MCP Tool Server
          </span>
          <span className="text-slate-200">
            {mcpTools ? `${mcpTools.tool_count} tools` : "—"}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span>Adapter Mode</span>
          <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-amber-300">
            {health?.integration_mode ?? "mock"}
          </span>
        </div>
      </div>
    </aside>
  );
}
