"""Disruption Agent: detects and verifies flight cancellations/delays via MCP telemetry."""

from datetime import datetime, timezone
import uuid
from app.integrations.mcp.client import RippleMCPClient
from app.schemas.trip import DisruptionEvent, NodeType, TripItinerary


class DisruptionAgent:
    """Detects a disruption event on a trip node and verifies it against flight telemetry."""

    def __init__(self, mcp_client: RippleMCPClient):
        self.mcp = mcp_client

    async def detect_disruption(
        self,
        itinerary: TripItinerary,
        node_id: str | None = None,
        disruption_type: str = "CANCELLATION",
        delay_minutes: int = 0,
        reason: str = "Operational crew constraint & severe weather at hub",
    ) -> DisruptionEvent:
        target_node = None
        if node_id:
            target_node = next((n for n in itinerary.nodes if n.id == node_id), None)
        if target_node is None:
            target_node = next(
                (n for n in itinerary.nodes if n.node_type == NodeType.FLIGHT),
                itinerary.nodes[0],
            )

        severity = "CRITICAL" if disruption_type == "CANCELLATION" or delay_minutes >= 90 else "HIGH"
        return DisruptionEvent(
            id=f"dis_{uuid.uuid4().hex[:8]}",
            trip_id=itinerary.id,
            node_id=target_node.id,
            disruption_type=disruption_type,  # type: ignore[arg-type]
            severity=severity,  # type: ignore[arg-type]
            reason=reason,
            source="Airline Operations Alert / MCP Telemetry",
            verified=False,
            delay_minutes=delay_minutes,
            detected_at=datetime.now(timezone.utc),
        )

    async def verify_disruption(
        self, itinerary: TripItinerary, disruption: DisruptionEvent
    ) -> DisruptionEvent:
        node = next((n for n in itinerary.nodes if n.id == disruption.node_id), None)
        if not node:
            return disruption

        flight_no = str(node.metadata.get("flight_number", node.booking_reference))
        telemetry = await self.mcp.call_tool(
            "flight_get_status",
            {"flight_number": flight_no, "pnr": node.booking_reference},
        )
        if isinstance(telemetry, dict):
            disruption.verified = bool(telemetry.get("verified", True))
            if telemetry.get("operational_status") == "CANCELLED":
                disruption.disruption_type = "CANCELLATION"
                disruption.reason = telemetry.get("reason", disruption.reason)
                disruption.source = telemetry.get("source", disruption.source)
        else:
            disruption.verified = True
        return disruption
