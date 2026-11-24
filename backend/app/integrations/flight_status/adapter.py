"""Flight status & alternative inventory adapter interface with mock implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class FlightStatusAdapter(ABC):
    """Contract for verifying live flight status and querying alternative flights."""

    @property
    @abstractmethod
    def mode(self) -> str:
        """Returns 'MOCK' or 'LIVE'."""

    @abstractmethod
    async def get_flight_status(self, flight_number: str, pnr: str) -> Dict[str, Any]:
        """Verify operational flight status from carrier/GDS telemetry."""

    @abstractmethod
    async def search_alternative_routes(
        self, origin: str, destination: str, earliest_departure_iso: str
    ) -> List[Dict[str, Any]]:
        """Return candidate replacement flight options clearly marked with inventory source."""


class MockFlightStatusAdapter(FlightStatusAdapter):
    """Mock flight telemetry and candidate route inventory for BLR -> DEL recovery."""

    @property
    def mode(self) -> str:
        return "MOCK"

    async def get_flight_status(self, flight_number: str, pnr: str) -> Dict[str, Any]:
        cancelled_flights = {"6E-512"}
        is_cancelled = flight_number in cancelled_flights
        return {
            "flight_number": flight_number,
            "pnr": pnr,
            "operational_status": "CANCELLED" if is_cancelled else "SCHEDULED",
            "verified": True,
            "delay_minutes": 0,
            "reason": (
                "ATC slot restriction & inbound aircraft crew timeout at BLR"
                if is_cancelled
                else "Operating on schedule"
            ),
            "source": "Mock FlightAware / DGCA Telemetry Feed",
            "adapter_mode": self.mode,
        }

    async def search_alternative_routes(
        self, origin: str, destination: str, earliest_departure_iso: str
    ) -> List[Dict[str, Any]]:
        # Candidate replacement flights for BLR -> DEL recovery
        return [
            {
                "option_id": "opt_direct_morning",
                "label": "Option 1 · Air India Direct Early Morning (AI-804)",
                "route_description": f"{origin} → {destination} (Non-stop)",
                "carrier_codes": ["AI-804"],
                "departure_time": "2026-11-26T05:45:00+05:30",
                "arrival_time": "2026-11-26T08:25:00+05:30",
                "fare_inr": 9400.0,
                "refund_credit_inr": 5800.0,
                "stops": 0,
                "cabin_class": "ECONOMY",
                "seats_available": 4,
                "inventory_mode": "MOCK_INVENTORY",
            },
            {
                "option_id": "opt_via_hyd",
                "label": "Option 2 · IndiGo Overnight via Hyderabad (6E-403 + 6E-612)",
                "route_description": f"{origin} → HYD → {destination} (1 Stop · 1h45m layover)",
                "carrier_codes": ["6E-403", "6E-612"],
                "departure_time": "2026-11-25T22:30:00+05:30",
                "arrival_time": "2026-11-26T03:45:00+05:30",
                "fare_inr": 11800.0,
                "refund_credit_inr": 5800.0,
                "stops": 1,
                "cabin_class": "ECONOMY",
                "seats_available": 3,
                "inventory_mode": "MOCK_INVENTORY",
            },
            {
                "option_id": "opt_late_direct",
                "label": "Option 3 · IndiGo Low-Fare Direct (6E-209)",
                "route_description": f"{origin} → {destination} (Non-stop)",
                "carrier_codes": ["6E-209"],
                "departure_time": "2026-11-26T07:30:00+05:30",
                "arrival_time": "2026-11-26T10:15:00+05:30",
                "fare_inr": 6800.0,
                "refund_credit_inr": 5800.0,
                "stops": 0,
                "cabin_class": "ECONOMY",
                "seats_available": 9,
                "inventory_mode": "MOCK_INVENTORY",
            },
            {
                "option_id": "opt_business_redeye",
                "label": "Option 4 · Air India Business Red-Eye (AI-505)",
                "route_description": f"{origin} → {destination} (Non-stop · Business Class)",
                "carrier_codes": ["AI-505"],
                "departure_time": "2026-11-25T23:55:00+05:30",
                "arrival_time": "2026-11-26T02:40:00+05:30",
                "fare_inr": 28500.0,
                "refund_credit_inr": 5800.0,
                "stops": 0,
                "cabin_class": "BUSINESS",
                "seats_available": 2,
                "inventory_mode": "MOCK_INVENTORY",
            },
        ]
