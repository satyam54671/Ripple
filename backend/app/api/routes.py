"""FastAPI REST API routes for trips, disruptions, LangGraph workflows, and MCP inspection."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.integrations.mcp.client import RippleMCPClient
from app.schemas.trip import (
    ApprovalDecisionRequest,
    RecoveryWorkflowResponse,
    TriggerDisruptionRequest,
    TripItinerary,
)
from app.services import trip_service
from app.workflows.recovery_workflow import RippleRecoveryOrchestrator

router = APIRouter()
mcp_client = RippleMCPClient()
orchestrator = RippleRecoveryOrchestrator(mcp_client=mcp_client)


@router.get("/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "integration_mode": settings.integration_mode,
        "database_engine": "sqlite" if settings.database_url.startswith("sqlite") else "postgresql",
    }


@router.get("/trips", response_model=list[TripItinerary])
async def get_trips(db: Session = Depends(get_db)):
    return trip_service.list_trips(db)


@router.get("/trips/{trip_id}", response_model=TripItinerary)
async def get_trip_by_id(trip_id: str, db: Session = Depends(get_db)):
    trip = trip_service.get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip '{trip_id}' not found")
    return trip


@router.get("/trips/{trip_id}/workflow", response_model=RecoveryWorkflowResponse | None)
async def get_trip_workflow(trip_id: str, db: Session = Depends(get_db)):
    trip = trip_service.get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip '{trip_id}' not found")
    return trip_service.get_latest_workflow_run(db, trip_id)


@router.post("/trips/{trip_id}/disruptions", response_model=RecoveryWorkflowResponse)
async def trigger_disruption(
    trip_id: str,
    payload: TriggerDisruptionRequest,
    db: Session = Depends(get_db),
):
    trip = trip_service.get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip '{trip_id}' not found")

    workflow_res, updated_trip = await orchestrator.start_recovery(
        itinerary=trip,
        node_id=payload.node_id,
        disruption_type=payload.disruption_type,
        delay_minutes=payload.delay_minutes,
        reason=payload.reason,
    )
    trip_service.save_itinerary(db, updated_trip)
    trip_service.save_workflow_run(db, workflow_res)
    return workflow_res


@router.post("/demo/trigger-cancellation", response_model=RecoveryWorkflowResponse)
async def trigger_demo_cancellation(db: Session = Depends(get_db)):
    """Reset the BLR->BOM->DEL demo itinerary and simulate IndiGo 6E-512 cancellation."""
    demo_trip = trip_service.reset_demo_trip(db)
    workflow_res, updated_trip = await orchestrator.start_recovery(
        itinerary=demo_trip,
        node_id="flt_blr_bom",
        disruption_type="CANCELLATION",
        delay_minutes=0,
        reason="ATC slot restriction & inbound aircraft crew timeout at BLR",
    )
    trip_service.save_itinerary(db, updated_trip)
    trip_service.save_workflow_run(db, workflow_res)
    return workflow_res


@router.post("/demo/reset", response_model=TripItinerary)
async def reset_demo(db: Session = Depends(get_db)):
    """Reset the primary BLR->BOM->DEL demo scenario back to its clean ON_TRACK baseline."""
    return trip_service.reset_demo_trip(db)


@router.post("/workflows/{run_id}/approve", response_model=RecoveryWorkflowResponse)
async def approve_recovery_workflow(
    run_id: str,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
):
    prior_run = trip_service.get_workflow_run_by_id(db, run_id)
    if not prior_run:
        raise HTTPException(status_code=404, detail=f"Workflow run '{run_id}' not found")

    if prior_run.approval_status == "EXECUTED":
        raise HTTPException(status_code=400, detail="Recovery plan already executed")

    trip = trip_service.get_trip(db, prior_run.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip '{prior_run.trip_id}' not found")

    workflow_res, updated_trip = await orchestrator.submit_human_decision(
        itinerary=trip,
        prior_run=prior_run,
        option_id=payload.option_id,
        decision=payload.decision,
    )
    trip_service.save_itinerary(db, updated_trip)
    trip_service.save_workflow_run(db, workflow_res)
    return workflow_res


@router.get("/mcp/tools")
async def list_mcp_tools():
    tools = await mcp_client.list_available_tools()
    return {"server": "ripple-travel-tools", "tool_count": len(tools), "tools": tools}
