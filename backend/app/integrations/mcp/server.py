"""
RIPPLE MCP Server built with the official Model Context Protocol (MCP) SDK.

Exposes standardized tools across Gmail, Google Calendar, Flight Telemetry, and
Travel Provider Booking APIs. Can run standalone via stdio/SSE or be invoked
in-process by RippleMCPClient.
"""

from typing import Any, Dict, List
from mcp.server.mcpserver import MCPServer

from app.integrations.calendar.adapter import GoogleCalendarAdapter, MockGoogleCalendarAdapter
from app.integrations.flight_status.adapter import FlightStatusAdapter, MockFlightStatusAdapter
from app.integrations.gmail.adapter import GmailAdapter, MockGmailAdapter
from app.integrations.travel_provider.adapter import (
    MockTravelProviderAdapter,
    TravelProviderAdapter,
)


def create_ripple_mcp_server(
    gmail: GmailAdapter | None = None,
    calendar: GoogleCalendarAdapter | None = None,
    flight_status: FlightStatusAdapter | None = None,
    travel_provider: TravelProviderAdapter | None = None,
) -> MCPServer:
    """Create and register all RIPPLE tools on an MCPServer instance."""
    gmail_adapter = gmail or MockGmailAdapter()
    calendar_adapter = calendar or MockGoogleCalendarAdapter()
    flight_adapter = flight_status or MockFlightStatusAdapter()
    provider_adapter = travel_provider or MockTravelProviderAdapter()

    mcp = MCPServer(
        name="ripple-travel-tools",
        instructions=(
            "Standardized MCP toolset for travel itinerary extraction, disruption verification, "
            "calendar commitment checks, and human-approved booking recovery."
        ),
    )

    @mcp.tool(description="Retrieve travel booking confirmation emails from Gmail.")
    async def gmail_fetch_confirmations(traveller_email: str) -> List[Dict[str, Any]]:
        return await gmail_adapter.fetch_booking_confirmations(traveller_email)

    @mcp.tool(description="List upcoming meetings and hard commitments from Google Calendar.")
    async def calendar_list_commitments(
        traveller_email: str, trip_id: str
    ) -> List[Dict[str, Any]]:
        return await calendar_adapter.list_upcoming_commitments(traveller_email, trip_id)

    @mcp.tool(description="Send a schedule advisory for a Google Calendar commitment.")
    async def calendar_send_advisory(event_id: str, message: str) -> Dict[str, Any]:
        return await calendar_adapter.send_meeting_advisory(event_id, message)

    @mcp.tool(description="Check live operational flight status and verify disruption.")
    async def flight_get_status(flight_number: str, pnr: str) -> Dict[str, Any]:
        return await flight_adapter.get_flight_status(flight_number, pnr)

    @mcp.tool(description="Search alternative flight routes for disruption recovery.")
    async def flight_search_alternatives(
        origin: str, destination: str, earliest_departure_iso: str
    ) -> List[Dict[str, Any]]:
        return await flight_adapter.search_alternative_routes(
            origin, destination, earliest_departure_iso
        )

    @mcp.tool(description="Book an approved replacement flight itinerary (requires human approval).")
    async def travel_book_flight(
        carrier_codes: List[str],
        traveller_name: str,
        departure_time: str,
        arrival_time: str,
    ) -> Dict[str, Any]:
        return await provider_adapter.book_replacement_flight(
            carrier_codes, traveller_name, departure_time, arrival_time
        )

    @mcp.tool(description="Cancel an unreachable connecting flight segment (requires human approval).")
    async def travel_cancel_flight(booking_reference: str, reason: str) -> Dict[str, Any]:
        return await provider_adapter.cancel_missed_flight(booking_reference, reason)

    @mcp.tool(description="Reschedule an airport transfer pickup window (requires human approval).")
    async def travel_reschedule_transfer(
        booking_reference: str, new_pickup_time: str
    ) -> Dict[str, Any]:
        return await provider_adapter.reschedule_transfer(booking_reference, new_pickup_time)

    @mcp.tool(description="Notify hotel of updated arrival / late check-in hold (requires human approval).")
    async def travel_notify_hotel(
        booking_reference: str, expected_arrival: str
    ) -> Dict[str, Any]:
        return await provider_adapter.notify_hotel_late_checkin(
            booking_reference, expected_arrival
        )

    return mcp


# Default singleton MCP server for in-process client calls and standalone CLI execution
ripple_mcp_server = create_ripple_mcp_server()

if __name__ == "__main__":
    ripple_mcp_server.run()
