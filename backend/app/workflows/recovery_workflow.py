"""
Stateful LangGraph Recovery Workflow for RIPPLE.

Pipeline:
START -> DETECT_DISRUPTION -> VERIFY_DISRUPTION -> (conditional)
  -> ANALYSE_IMPACT -> GENERATE_RECOVERY_OPTIONS -> OPTIMISE
  -> HUMAN_APPROVAL (LangGraph interrupt checkpoint)
  -> EXECUTE -> VERIFY_EXECUTION -> END
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, TypedDict
import uuid

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.disruption_agent import DisruptionAgent
from app.agents.impact_analysis_agent import ImpactAnalysisAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.agents.recovery_agent import RecoveryAgent
from app.agents.verification_agent import VerificationAgent
from app.integrations.mcp.client import RippleMCPClient
from app.schemas.trip import (
    BookingStatus,
    DisruptionEvent,
    ExecutionActionLog,
    ImpactAnalysisResult,
    NodeType,
    RecoveryOption,
    RecoveryWorkflowResponse,
    TripItinerary,
    TripStatus,
    WorkflowTraceEntry,
)


class RecoveryGraphState(TypedDict, total=False):
    run_id: str
    trip_id: str
    itinerary: Dict[str, Any]
    target_node_id: Optional[str]
    disruption_type: str
    delay_minutes: int
    reason: str
    current_stage: str
    itinerary_context: Dict[str, Any]
    disruption: Optional[Dict[str, Any]]
    impact_analysis: Optional[Dict[str, Any]]
    candidate_routes: List[Dict[str, Any]]
    recovery_options: List[Dict[str, Any]]
    recommended_option_id: Optional[str]
    approval_status: str  # PENDING | APPROVED | REJECTED | EXECUTED
    selected_option_id: Optional[str]
    execution_logs: List[Dict[str, Any]]
    verification_passed: bool
    verification_summary: str
    workflow_trace: List[Dict[str, Any]]


def _trace(
    stage: str,
    agent: str,
    status: Literal["COMPLETED", "WAITING_APPROVAL", "FAILED", "SKIPPED"],
    message: str,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return WorkflowTraceEntry(
        stage=stage,
        agent=agent,
        status=status,
        message=message,
        timestamp=datetime.now(timezone.utc),
        details=details or {},
    ).model_dump(mode="json")


class RippleRecoveryOrchestrator:
    """Compiles and executes the stateful LangGraph recovery workflow."""

    def __init__(self, mcp_client: RippleMCPClient | None = None):
        self.mcp = mcp_client or RippleMCPClient()
        self.itinerary_agent = ItineraryAgent(self.mcp)
        self.disruption_agent = DisruptionAgent(self.mcp)
        self.impact_agent = ImpactAnalysisAgent()
        self.recovery_agent = RecoveryAgent(self.mcp)
        self.verification_agent = VerificationAgent()
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(RecoveryGraphState)

        builder.add_node("detect_disruption", self._node_detect_disruption)
        builder.add_node("verify_disruption", self._node_verify_disruption)
        builder.add_node("analyse_impact", self._node_analyse_impact)
        builder.add_node("generate_recovery_options", self._node_generate_options)
        builder.add_node("optimise_recovery", self._node_optimise)
        builder.add_node("human_approval", self._node_human_approval)
        builder.add_node("execute_recovery", self._node_execute)
        builder.add_node("verify_execution", self._node_verify_execution)

        builder.add_edge(START, "detect_disruption")
        builder.add_edge("detect_disruption", "verify_disruption")
        builder.add_conditional_edges(
            "verify_disruption",
            self._route_after_verification,
            {
                "verified": "analyse_impact",
                "false_alarm": END,
            },
        )
        builder.add_edge("analyse_impact", "generate_recovery_options")
        builder.add_edge("generate_recovery_options", "optimise_recovery")
        builder.add_edge("optimise_recovery", "human_approval")
        builder.add_conditional_edges(
            "human_approval",
            self._route_after_approval,
            {
                "approved": "execute_recovery",
                "rejected": END,
            },
        )
        builder.add_edge("execute_recovery", "verify_execution")
        builder.add_edge("verify_execution", END)

        # Pause right at the human_approval node before any irreversible booking action
        return builder.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["human_approval"],
        )

    async def _node_detect_disruption(self, state: RecoveryGraphState) -> Dict[str, Any]:
        itinerary = TripItinerary(**state["itinerary"])
        context = await self.itinerary_agent.enrich_itinerary_context(itinerary)
        disruption = await self.disruption_agent.detect_disruption(
            itinerary=itinerary,
            node_id=state.get("target_node_id"),
            disruption_type=state.get("disruption_type", "CANCELLATION"),
            delay_minutes=state.get("delay_minutes", 0),
            reason=state.get("reason", "Operational disruption"),
        )
        trace = list(state.get("workflow_trace", []))
        trace.append(
            _trace(
                stage="DETECT_DISRUPTION",
                agent="DisruptionAgent + ItineraryAgent",
                status="COMPLETED",
                message=(
                    f"Detected {disruption.disruption_type} on {disruption.node_id}; "
                    f"synced {context['email_confirmations_count']} Gmail confirmations & "
                    f"{context['calendar_commitments_count']} Calendar commitments via MCP."
                ),
            )
        )
        return {
            "current_stage": "DETECT_DISRUPTION",
            "itinerary_context": context,
            "disruption": disruption.model_dump(mode="json"),
            "workflow_trace": trace,
        }

    async def _node_verify_disruption(self, state: RecoveryGraphState) -> Dict[str, Any]:
        itinerary = TripItinerary(**state["itinerary"])
        disruption = DisruptionEvent(**state["disruption"])
        verified = await self.disruption_agent.verify_disruption(itinerary, disruption)
        trace = list(state.get("workflow_trace", []))
        trace.append(
            _trace(
                stage="VERIFY_DISRUPTION",
                agent="DisruptionAgent",
                status="COMPLETED",
                message=(
                    f"Verified {verified.disruption_type} via MCP flight telemetry: "
                    f"{verified.reason}"
                ),
            )
        )
        return {
            "current_stage": "VERIFY_DISRUPTION",
            "disruption": verified.model_dump(mode="json"),
            "workflow_trace": trace,
        }

    def _route_after_verification(self, state: RecoveryGraphState) -> str:
        disruption = state.get("disruption") or {}
        return "verified" if disruption.get("verified", False) else "false_alarm"

    async def _node_analyse_impact(self, state: RecoveryGraphState) -> Dict[str, Any]:
        itinerary = TripItinerary(**state["itinerary"])
        disruption = DisruptionEvent(**state["disruption"])
        impact = self.impact_agent.analyze(itinerary, disruption)
        trace = list(state.get("workflow_trace", []))
        trace.append(
            _trace(
                stage="ANALYSE_IMPACT",
                agent="ImpactAnalysisAgent",
                status="COMPLETED",
                message=impact.summary,
                details={"total_affected": impact.total_affected},
            )
        )
        return {
            "current_stage": "ANALYSE_IMPACT",
            "impact_analysis": impact.model_dump(mode="json"),
            "workflow_trace": trace,
        }

    async def _node_generate_options(self, state: RecoveryGraphState) -> Dict[str, Any]:
        itinerary = TripItinerary(**state["itinerary"])
        impact = ImpactAnalysisResult(**state["impact_analysis"])
        candidates = await self.recovery_agent.generate_candidates(itinerary, impact)
        trace = list(state.get("workflow_trace", []))
        trace.append(
            _trace(
                stage="GENERATE_RECOVERY_OPTIONS",
                agent="RecoveryAgent",
                status="COMPLETED",
                message=(
                    f"Retrieved {len(candidates)} candidate recovery routes via MCP "
                    "(tagged MOCK_INVENTORY)."
                ),
            )
        )
        return {
            "current_stage": "GENERATE_RECOVERY_OPTIONS",
            "candidate_routes": candidates,
            "workflow_trace": trace,
        }

    async def _node_optimise(self, state: RecoveryGraphState) -> Dict[str, Any]:
        itinerary = TripItinerary(**state["itinerary"])
        impact = ImpactAnalysisResult(**state["impact_analysis"])
        options = self.recovery_agent.optimize_options(
            itinerary, impact, state.get("candidate_routes", [])
        )
        recommended = next((o for o in options if o.is_recommended), options[0] if options else None)
        trace = list(state.get("workflow_trace", []))
        trace.append(
            _trace(
                stage="OPTIMISE",
                agent="RecoveryOptimizer (OR-Tools CP-SAT)",
                status="COMPLETED",
                message=(
                    f"Ranked {len(options)} plans; recommended '{recommended.label}' "
                    f"(score {recommended.optimizer_score}/100)."
                    if recommended
                    else "No recovery options evaluated."
                ),
            )
        )
        trace.append(
            _trace(
                stage="HUMAN_APPROVAL",
                agent="HumanInTheLoopGate",
                status="WAITING_APPROVAL",
                message=(
                    "Workflow paused before booking/modification. Awaiting human approval."
                ),
            )
        )
        return {
            "current_stage": "HUMAN_APPROVAL",
            "recovery_options": [o.model_dump(mode="json") for o in options],
            "recommended_option_id": recommended.id if recommended else None,
            "selected_option_id": recommended.id if recommended else None,
            "approval_status": "PENDING",
            "workflow_trace": trace,
        }

    async def _node_human_approval(self, state: RecoveryGraphState) -> Dict[str, Any]:
        approval_status = state.get("approval_status", "PENDING")
        trace = list(state.get("workflow_trace", []))
        if approval_status == "APPROVED":
            trace.append(
                _trace(
                    stage="HUMAN_APPROVAL",
                    agent="HumanReviewer",
                    status="COMPLETED",
                    message=(
                        f"Human approved recovery option '{state.get('selected_option_id')}'."
                    ),
                )
            )
        else:
            trace.append(
                _trace(
                    stage="HUMAN_APPROVAL",
                    agent="HumanReviewer",
                    status="SKIPPED",
                    message="Recovery plan rejected by human reviewer. No bookings modified.",
                )
            )
        return {
            "current_stage": "HUMAN_APPROVAL" if approval_status != "APPROVED" else "EXECUTE",
            "workflow_trace": trace,
        }

    def _route_after_approval(self, state: RecoveryGraphState) -> str:
        return "approved" if state.get("approval_status") == "APPROVED" else "rejected"

    async def _node_execute(self, state: RecoveryGraphState) -> Dict[str, Any]:
        itinerary = TripItinerary(**state["itinerary"])
        options = [RecoveryOption(**o) for o in state.get("recovery_options", [])]
        selected_id = state.get("selected_option_id") or state.get("recommended_option_id")
        selected = next((o for o in options if o.id == selected_id), options[0])
        logs = await self.recovery_agent.execute_approved_plan(itinerary, selected)
        trace = list(state.get("workflow_trace", []))
        trace.append(
            _trace(
                stage="EXECUTE",
                agent="RecoveryAgent (MCP TravelProvider)",
                status="COMPLETED",
                message=f"Executed {len(logs)} approved recovery action(s) via MCP mock adapters.",
            )
        )
        return {
            "current_stage": "EXECUTE",
            "execution_logs": [l.model_dump(mode="json") for l in logs],
            "workflow_trace": trace,
        }

    async def _node_verify_execution(self, state: RecoveryGraphState) -> Dict[str, Any]:
        itinerary = TripItinerary(**state["itinerary"])
        options = [RecoveryOption(**o) for o in state.get("recovery_options", [])]
        selected_id = state.get("selected_option_id") or state.get("recommended_option_id")
        selected = next((o for o in options if o.id == selected_id), options[0])
        logs = [ExecutionActionLog(**l) for l in state.get("execution_logs", [])]
        passed, summary, verified_logs = self.verification_agent.verify_execution(
            itinerary, selected, logs
        )
        trace = list(state.get("workflow_trace", []))
        trace.append(
            _trace(
                stage="VERIFY_EXECUTION",
                agent="VerificationAgent",
                status="COMPLETED" if passed else "FAILED",
                message=summary,
            )
        )
        return {
            "current_stage": "COMPLETED",
            "approval_status": "EXECUTED",
            "execution_logs": [l.model_dump(mode="json") for l in verified_logs],
            "verification_passed": passed,
            "verification_summary": summary,
            "workflow_trace": trace,
        }

    async def start_recovery(
        self,
        itinerary: TripItinerary,
        node_id: Optional[str] = None,
        disruption_type: str = "CANCELLATION",
        delay_minutes: int = 0,
        reason: str = "Operational crew constraint & severe weather at hub",
    ) -> tuple[RecoveryWorkflowResponse, TripItinerary]:
        """Run the workflow from START until the HUMAN_APPROVAL checkpoint."""
        run_id = f"run_{uuid.uuid4().hex[:10]}"
        config = {"configurable": {"thread_id": run_id}}

        initial_state: RecoveryGraphState = {
            "run_id": run_id,
            "trip_id": itinerary.id,
            "itinerary": itinerary.model_dump(mode="json"),
            "target_node_id": node_id,
            "disruption_type": disruption_type,
            "delay_minutes": delay_minutes,
            "reason": reason,
            "current_stage": "START",
            "approval_status": "PENDING",
            "workflow_trace": [],
        }

        final_state = await self.graph.ainvoke(initial_state, config=config)
        updated_itinerary = self._apply_disruption_to_itinerary(itinerary, final_state)
        return self._state_to_response(final_state), updated_itinerary

    async def submit_human_decision(
        self,
        itinerary: TripItinerary,
        prior_run: RecoveryWorkflowResponse,
        option_id: str,
        decision: Literal["APPROVE", "REJECT"],
    ) -> tuple[RecoveryWorkflowResponse, TripItinerary]:
        """Resume the paused LangGraph workflow after human approval or rejection."""
        config = {"configurable": {"thread_id": prior_run.run_id}}
        approval_status = "APPROVED" if decision == "APPROVE" else "REJECTED"

        # Check if LangGraph checkpoint exists in memory; if not (e.g., server restart), run tail nodes cleanly
        snapshot = self.graph.get_state(config)
        if snapshot and snapshot.values:
            self.graph.update_state(
                config,
                {
                    "approval_status": approval_status,
                    "selected_option_id": option_id,
                },
            )
            final_state = await self.graph.ainvoke(None, config=config)
        else:
            state: RecoveryGraphState = {
                "run_id": prior_run.run_id,
                "trip_id": prior_run.trip_id,
                "itinerary": itinerary.model_dump(mode="json"),
                "current_stage": prior_run.current_stage,
                "disruption": prior_run.disruption.model_dump(mode="json")
                if prior_run.disruption
                else None,
                "impact_analysis": prior_run.impact_analysis.model_dump(mode="json")
                if prior_run.impact_analysis
                else None,
                "recovery_options": [o.model_dump(mode="json") for o in prior_run.recovery_options],
                "recommended_option_id": prior_run.recommended_option_id,
                "selected_option_id": option_id,
                "approval_status": approval_status,
                "workflow_trace": [t.model_dump(mode="json") for t in prior_run.workflow_trace],
            }
            approval_delta = await self._node_human_approval(state)
            state.update(approval_delta)
            if approval_status == "APPROVED":
                exec_delta = await self._node_execute(state)
                state.update(exec_delta)
                verify_delta = await self._node_verify_execution(state)
                state.update(verify_delta)
            final_state = state

        response = self._state_to_response(final_state)
        updated_itinerary = self._apply_execution_to_itinerary(itinerary, response)
        return response, updated_itinerary

    def _apply_disruption_to_itinerary(
        self, itinerary: TripItinerary, state: Dict[str, Any]
    ) -> TripItinerary:
        impact_raw = state.get("impact_analysis")
        if not impact_raw:
            return itinerary
        impact = ImpactAnalysisResult(**impact_raw)
        impact_map = {r.node_id: r.impact_level for r in impact.impacted_nodes}

        updated_nodes = []
        for node in itinerary.nodes:
            level = impact_map.get(node.id, "UNAFFECTED")
            new_status = node.status
            if level == "ROOT_CAUSE":
                new_status = (
                    BookingStatus.CANCELLED
                    if state.get("disruption_type") == "CANCELLATION"
                    else BookingStatus.DELAYED
                )
            elif level == "BROKEN":
                new_status = BookingStatus.MISSED_CONNECTION
            elif level in {"AT_RISK", "NEEDS_UPDATE"}:
                new_status = BookingStatus.AT_RISK
            updated_nodes.append(node.model_copy(update={"status": new_status}))

        return itinerary.model_copy(
            update={"status": TripStatus.AWAITING_APPROVAL, "nodes": updated_nodes}
        )

    def _apply_execution_to_itinerary(
        self, itinerary: TripItinerary, response: RecoveryWorkflowResponse
    ) -> TripItinerary:
        if response.approval_status == "REJECTED":
            return itinerary.model_copy(update={"status": TripStatus.DISRUPTED})

        if response.approval_status != "EXECUTED":
            return itinerary

        selected = next(
            (o for o in response.recovery_options if o.id == response.selected_option_id),
            None,
        )
        if not selected:
            return itinerary

        updated_nodes = []
        for node in itinerary.nodes:
            if node.id == (response.disruption.node_id if response.disruption else "flt_blr_bom"):
                updated_nodes.append(
                    node.model_copy(
                        update={
                            "title": f"Rebooked: {' + '.join(selected.carrier_codes)} ({selected.route_description})",
                            "start_time": selected.departure_time,
                            "end_time": selected.arrival_time,
                            "status": BookingStatus.REBOOKED,
                            "cost_inr": selected.additional_cost_inr,
                        }
                    )
                )
            elif node.id == "flt_bom_del":
                updated_nodes.append(
                    node.model_copy(update={"status": BookingStatus.CANCELLED})
                )
            elif node.node_type == NodeType.TRANSFER:
                new_pickup = selected.arrival_time + timedelta(minutes=25)
                updated_nodes.append(
                    node.model_copy(
                        update={
                            "start_time": new_pickup,
                            "end_time": new_pickup + timedelta(minutes=45),
                            "status": BookingStatus.RESCHEDULED,
                        }
                    )
                )
            elif node.node_type == NodeType.HOTEL:
                updated_nodes.append(
                    node.model_copy(update={"status": BookingStatus.CONFIRMED})
                )
            elif node.node_type == NodeType.MEETING:
                updated_nodes.append(
                    node.model_copy(
                        update={
                            "status": BookingStatus.CONFIRMED
                            if selected.preserves_meeting
                            else BookingStatus.AT_RISK
                        }
                    )
                )
            else:
                updated_nodes.append(node)

        return itinerary.model_copy(
            update={"status": TripStatus.RECOVERED, "nodes": updated_nodes}
        )

    def _state_to_response(self, state: Dict[str, Any]) -> RecoveryWorkflowResponse:
        return RecoveryWorkflowResponse(
            run_id=state["run_id"],
            trip_id=state["trip_id"],
            current_stage=state.get("current_stage", "START"),
            approval_status=state.get("approval_status", "PENDING"),  # type: ignore[arg-type]
            disruption=DisruptionEvent(**state["disruption"]) if state.get("disruption") else None,
            impact_analysis=ImpactAnalysisResult(**state["impact_analysis"])
            if state.get("impact_analysis")
            else None,
            recovery_options=[RecoveryOption(**o) for o in state.get("recovery_options", [])],
            recommended_option_id=state.get("recommended_option_id"),
            selected_option_id=state.get("selected_option_id"),
            execution_logs=[ExecutionActionLog(**l) for l in state.get("execution_logs", [])],
            verification_passed=bool(state.get("verification_passed", False)),
            verification_summary=state.get("verification_summary", ""),
            workflow_trace=[WorkflowTraceEntry(**t) for t in state.get("workflow_trace", [])],
        )
