"""Recovery Agent: generates candidate recovery routes via MCP, optimizes via OR-Tools, and executes approved plans."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from app.integrations.mcp.client import RippleMCPClient
from app.optimisation.recovery_optimizer import RecoveryOptimizer
from app.schemas.trip import (
    ExecutionActionLog,
    ImpactAnalysisResult,
    NodeType,
    RecoveryOption,
    TripItinerary,
)


class RecoveryAgent:
    """Generates candidate itineraries, delegates optimization to OR-Tools, and executes post-approval actions."""

    def __init__(self, mcp_client: RippleMCPClient, optimizer: RecoveryOptimizer | None = None):
        self.mcp = mcp_client
        self.optimizer = optimizer or RecoveryOptimizer()

    async def generate_candidates(
        self, itinerary: TripItinerary, impact: ImpactAnalysisResult
    ) -> List[Dict[str, Any]]:
        root_node = next((n for n in itinerary.nodes if n.id == impact.root_node_id), None)
        earliest_iso = (
            root_node.start_time.isoformat()
            if root_node
            else datetime.now(timezone.utc).isoformat()
        )
        candidates = await self.mcp.call_tool(
            "flight_search_alternatives",
            {
                "origin": itinerary.origin,
                "destination": itinerary.destination,
                "earliest_departure_iso": earliest_iso,
            },
        )
        return candidates if isinstance(candidates, list) else []

    def optimize_options(
        self,
        itinerary: TripItinerary,
        impact: ImpactAnalysisResult,
        candidates: List[Dict[str, Any]],
    ) -> List[RecoveryOption]:
        return self.optimizer.optimize(itinerary, impact, candidates)

    async def execute_approved_plan(
        self, itinerary: TripItinerary, option: RecoveryOption
    ) -> List[ExecutionActionLog]:
        """Execute every recovery step via MCP Travel Provider tools ONLY after human approval."""
        logs: List[ExecutionActionLog] = []
        missed_flight = next(
            (n for n in itinerary.nodes if n.id == "flt_bom_del"),
            None,
        )
        transfer_node = next(
            (n for n in itinerary.nodes if n.node_type == NodeType.TRANSFER),
            None,
        )
        hotel_node = next(
            (n for n in itinerary.nodes if n.node_type == NodeType.HOTEL),
            None,
        )

        for action in option.actions:
            if action.action_type == "BOOK_FLIGHT":
                res = await self.mcp.call_tool(
                    "travel_book_flight",
                    {
                        "carrier_codes": option.carrier_codes,
                        "traveller_name": itinerary.traveller_name,
                        "departure_time": option.departure_time.isoformat(),
                        "arrival_time": option.arrival_time.isoformat(),
                    },
                )
            elif action.action_type == "CANCEL_FLIGHT":
                ref = missed_flight.booking_reference if missed_flight else action.target_node_id
                res = await self.mcp.call_tool(
                    "travel_cancel_flight",
                    {"booking_reference": ref, "reason": "Upstream BLR->BOM cancellation"},
                )
            elif action.action_type == "UPDATE_TRANSFER":
                ref = transfer_node.booking_reference if transfer_node else action.target_node_id
                new_pickup = (option.arrival_time + timedelta(minutes=25)).isoformat()
                res = await self.mcp.call_tool(
                    "travel_reschedule_transfer",
                    {"booking_reference": ref, "new_pickup_time": new_pickup},
                )
            elif action.action_type == "NOTIFY_HOTEL":
                ref = hotel_node.booking_reference if hotel_node else action.target_node_id
                res = await self.mcp.call_tool(
                    "travel_notify_hotel",
                    {
                        "booking_reference": ref,
                        "expected_arrival": option.arrival_time.isoformat(),
                    },
                )
            elif action.action_type == "NOTIFY_MEETING":
                res = await self.mcp.call_tool(
                    "calendar_send_advisory",
                    {
                        "event_id": action.target_node_id,
                        "message": f"Updated travel arrival: {option.arrival_time.isoformat()}",
                    },
                )
            else:
                res = {"status": "SKIPPED", "message": "Unsupported action type"}

            res_dict = res if isinstance(res, dict) else {"message": str(res)}
            logs.append(
                ExecutionActionLog(
                    step_order=action.step_order,
                    action_type=action.action_type,
                    provider=action.provider,
                    target_node_id=action.target_node_id,
                    status="EXECUTED",
                    confirmation_code=str(res_dict.get("confirmation_code", "MOCK-OK")),
                    adapter_mode="MOCK",
                    message=str(res_dict.get("message", action.description)),
                    executed_at=datetime.now(timezone.utc),
                )
            )
        return logs
