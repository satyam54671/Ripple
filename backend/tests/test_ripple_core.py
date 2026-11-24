"""End-to-end tests for RIPPLE dependency graph, OR-Tools optimizer, MCP server, and LangGraph workflow."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.graph.trip_dependency_graph import TripDependencyGraph
from app.integrations.flight_status.adapter import MockFlightStatusAdapter
from app.integrations.mcp.client import RippleMCPClient
from app.main import app
from app.optimisation.recovery_optimizer import RecoveryOptimizer
from app.schemas.trip import DisruptionEvent
from app.services.sample_data import build_blr_bom_del_demo_trip


def test_dependency_graph_traces_cascade_impact():
    trip = build_blr_bom_del_demo_trip()
    graph = TripDependencyGraph(trip)
    disruption = DisruptionEvent(
        id="dis_test_1",
        trip_id=trip.id,
        node_id="flt_blr_bom",
        disruption_type="CANCELLATION",
        severity="CRITICAL",
        reason="Test cancellation",
        source="Test",
        verified=True,
        detected_at=datetime.now(timezone.utc),
    )

    impact = graph.trace_disruption_impact(disruption)
    levels = {r.node_id: r.impact_level for r in impact.impacted_nodes}

    assert levels["flt_blr_bom"] == "ROOT_CAUSE"
    assert levels["flt_bom_del"] == "BROKEN"
    assert levels["trf_del_hotel"] == "NEEDS_UPDATE"
    assert levels["htl_del_oberoi"] == "AT_RISK"
    assert levels["mtg_del_client"] == "AT_RISK"
    assert impact.total_affected == 4


@pytest.mark.asyncio
async def test_ortools_optimizer_ranks_feasible_direct_flight_highest():
    trip = build_blr_bom_del_demo_trip()
    graph = TripDependencyGraph(trip)
    disruption = DisruptionEvent(
        id="dis_test_2",
        trip_id=trip.id,
        node_id="flt_blr_bom",
        disruption_type="CANCELLATION",
        severity="CRITICAL",
        reason="Test cancellation",
        source="Test",
        verified=True,
        detected_at=datetime.now(timezone.utc),
    )
    impact = graph.trace_disruption_impact(disruption)
    candidates = await MockFlightStatusAdapter().search_alternative_routes(
        "BLR", "DEL", "2026-11-25T20:15:00+05:30"
    )

    options = RecoveryOptimizer().optimize(trip, impact, candidates)
    assert len(options) == 4

    recommended = next(o for o in options if o.is_recommended)
    assert recommended.id == "opt_direct_morning"
    assert recommended.preserves_meeting is True
    assert recommended.is_policy_compliant is True

    late_opt = next(o for o in options if o.id == "opt_late_direct")
    assert late_opt.meets_deadline is False

    biz_opt = next(o for o in options if o.id == "opt_business_redeye")
    assert biz_opt.is_policy_compliant is False


@pytest.mark.asyncio
async def test_mcp_server_lists_and_executes_tools():
    client = RippleMCPClient()
    tools = await client.list_available_tools()
    tool_names = {t["name"] for t in tools}
    assert {
        "gmail_fetch_confirmations",
        "calendar_list_commitments",
        "flight_get_status",
        "flight_search_alternatives",
        "travel_book_flight",
    }.issubset(tool_names)

    status = await client.call_tool(
        "flight_get_status", {"flight_number": "6E-512", "pnr": "RPL89K"}
    )
    assert status["operational_status"] == "CANCELLED"
    assert status["adapter_mode"] == "MOCK"


def test_full_api_demo_workflow_with_human_approval():
    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        # 1. Trigger demo cancellation -> pauses at HUMAN_APPROVAL
        trigger_res = client.post("/api/v1/demo/trigger-cancellation")
        assert trigger_res.status_code == 200
        wf = trigger_res.json()
        assert wf["current_stage"] == "HUMAN_APPROVAL"
        assert wf["approval_status"] == "PENDING"
        assert wf["recommended_option_id"] == "opt_direct_morning"
        assert wf["execution_logs"] == []

        # 2. Approve recommended option -> executes & verifies
        approve_res = client.post(
            f"/api/v1/workflows/{wf['run_id']}/approve",
            json={"option_id": wf["recommended_option_id"], "decision": "APPROVE"},
        )
        assert approve_res.status_code == 200
        done_wf = approve_res.json()
        assert done_wf["current_stage"] == "COMPLETED"
        assert done_wf["approval_status"] == "EXECUTED"
        assert done_wf["verification_passed"] is True
        assert len(done_wf["execution_logs"]) >= 4

        # 3. Verify trip is now RECOVERED
        trip_res = client.get("/api/v1/trips/trip_blr_bom_del_001")
        assert trip_res.status_code == 200
        assert trip_res.json()["status"] == "RECOVERED"

        # 4. Reset demo trip back to clean baseline
        reset_res = client.post("/api/v1/demo/reset")
        assert reset_res.status_code == 200
        assert reset_res.json()["status"] == "ON_TRACK"
