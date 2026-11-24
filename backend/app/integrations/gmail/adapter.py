"""Gmail integration interface and mock adapter for retrieving travel booking confirmations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class GmailAdapter(ABC):
    """Contract for retrieving travel confirmation emails from Gmail."""

    @property
    @abstractmethod
    def mode(self) -> str:
        """Returns 'MOCK' or 'LIVE'."""

    @abstractmethod
    async def fetch_booking_confirmations(self, traveller_email: str) -> List[Dict[str, Any]]:
        """Fetch parsed flight, hotel, and transfer confirmation payloads."""


class MockGmailAdapter(GmailAdapter):
    """Mock Gmail adapter returning structured booking emails for the BLR -> BOM -> DEL demo."""

    @property
    def mode(self) -> str:
        return "MOCK"

    async def fetch_booking_confirmations(self, traveller_email: str) -> List[Dict[str, Any]]:
        return [
            {
                "email_id": "msg_indigo_rpl89k",
                "subject": "IndiGo Itinerary & E-Ticket: BLR -> BOM (PNR: RPL89K)",
                "from": "reservations@goindigo.in",
                "to": traveller_email,
                "booking_type": "FLIGHT",
                "provider": "IndiGo Airlines",
                "flight_number": "6E-512",
                "pnr": "RPL89K",
                "origin": "BLR",
                "destination": "BOM",
                "departure_time": "2026-11-25T20:15:00+05:30",
                "arrival_time": "2026-11-25T22:00:00+05:30",
                "adapter_mode": self.mode,
            },
            {
                "email_id": "msg_airindia_ai442m",
                "subject": "Air India Booking Confirmation: BOM -> DEL (PNR: AI442M)",
                "from": "noreply@airindia.com",
                "to": traveller_email,
                "booking_type": "FLIGHT",
                "provider": "Air India",
                "flight_number": "AI-806",
                "pnr": "AI442M",
                "origin": "BOM",
                "destination": "DEL",
                "departure_time": "2026-11-25T23:15:00+05:30",
                "arrival_time": "2026-11-26T01:25:00+05:30",
                "adapter_mode": self.mode,
            },
            {
                "email_id": "msg_oberoi_99210",
                "subject": "The Oberoi, New Delhi — Reservation Confirmation #OBR-99210",
                "from": "reservations.delhi@oberoihotels.com",
                "to": traveller_email,
                "booking_type": "HOTEL",
                "provider": "Oberoi Hotels & Resorts",
                "booking_reference": "OBR-99210",
                "late_checkin_cutoff": "2026-11-26T04:00:00+05:30",
                "adapter_mode": self.mode,
            },
            {
                "email_id": "msg_blusmart_7741",
                "subject": "BluSmart Airport Pickup Scheduled #BLU-7741",
                "from": "rides@blu-smart.com",
                "to": traveller_email,
                "booking_type": "TRANSFER",
                "provider": "BluSmart Mobility",
                "booking_reference": "BLU-7741",
                "pickup_time": "2026-11-26T01:55:00+05:30",
                "adapter_mode": self.mode,
            },
        ]
