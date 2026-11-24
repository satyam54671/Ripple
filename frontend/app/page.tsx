"use client";

import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { DashboardView } from "@/components/DashboardView";
import { DisruptionAnalysisView } from "@/components/DisruptionAnalysisView";
import { RecoveryPlansView } from "@/components/RecoveryPlansView";
import { SidebarNav } from "@/components/SidebarNav";
import { TripDetailsView } from "@/components/TripDetailsView";
import { useRippleWorkspace } from "@/hooks/useRippleWorkspace";

export default function HomePage() {
  const {
    activeTab,
    setActiveTab,
    trips,
    selectedTrip,
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
  } = useRippleWorkspace();

  return (
    <div className="flex min-h-screen flex-col bg-[#050A14] text-slate-100 lg:flex-row">
      <SidebarNav
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onTriggerDemo={triggerDemoCancellation}
        onResetDemo={resetDemo}
        actionLoading={actionLoading}
        health={health}
        mcpTools={mcpTools}
        hasActiveWorkflow={Boolean(workflow)}
      />

      <main className="flex-1 p-5 sm:p-8 lg:max-w-[calc(100vw-18rem)]">
        {error && (
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-rose-500/40 bg-rose-950/30 px-4 py-3 text-sm text-rose-200">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => void refreshAll()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-rose-400/30 px-3 py-1 text-xs font-medium text-rose-100 hover:bg-rose-500/20"
            >
              <RefreshCw className="h-3.5 w-3.5" /> Retry
            </button>
          </div>
        )}

        {loading ? (
          <div className="flex h-64 items-center justify-center rounded-2xl border border-slate-800 bg-[#0B1324] text-sm text-slate-400">
            Loading RIPPLE workspace...
          </div>
        ) : (
          <>
            {activeTab === "dashboard" && (
              <DashboardView
                trips={trips}
                selectedTrip={selectedTrip}
                workflow={workflow}
                onSelectTrip={selectTrip}
                onNavigate={setActiveTab}
                onTriggerDemo={triggerDemoCancellation}
                actionLoading={actionLoading}
              />
            )}

            {activeTab === "trip-details" && (
              <TripDetailsView trip={selectedTrip} />
            )}

            {activeTab === "disruption-analysis" && (
              <DisruptionAnalysisView
                workflow={workflow}
                onNavigate={setActiveTab}
                onTriggerDemo={triggerDemoCancellation}
                actionLoading={actionLoading}
              />
            )}

            {activeTab === "recovery-plans" && (
              <RecoveryPlansView
                workflow={workflow}
                onApprove={submitApproval}
                onTriggerDemo={triggerDemoCancellation}
                actionLoading={actionLoading}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}
