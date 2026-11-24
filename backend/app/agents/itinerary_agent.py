"""Itinerary Agent: extracts and cross-references booking confirmations & calendar commitments via MCP."""

from typing import Any, Dict
from app.integrations.mcp.client import RippleMCPClient
from app.schemas.trip import TripItinerary


class ItineraryAgent:
    """Queries Gmail and Google Calendar MCP tools to verify unified itinerary context."""

    def __init__(self, mcp_client: RippleMCPClient):
        self.mcp = mcp_client

    async def enrich_itinerary_context(self, itinerary: TripItinerary) -> Dict[str, Any]:
        confirmations = await self.mcp.call_tool(
            "gmail_fetch_confirmations",
            {"traveller_email": itinerary.traveller_email},
        )
        commitments = await self.mcp.call_tool(
            "calendar_list_commitments",
            {"traveller_email": itinerary.traveller_email, "trip_id": itinerary.id},
        )
        return {
            "email_confirmations_count": len(confirmations) if isinstance(confirmations, list) else 0,
            "calendar_commitments_count": len(commitments) if isinstance(commitments, list) else 0,
            "confirmations": confirmations,
            "commitments": commitments,
        }
