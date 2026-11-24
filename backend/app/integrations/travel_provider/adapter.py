"""Travel provider booking/modification adapter interface with mock implementation."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict
import uuid


class TravelProviderAdapter(ABC):
    """
    Contract for executing booking, cancellation, transfer reschedule, and hotel updates.
    IMPORTANT: Every mutating method must only be invoked after explicit human approval.
    """

    @property
    @abstractmethod
    def mode(self) -> str:
        """Returns 'MOCK' or 'LIVE'."""

    @abstractmethod
    async def book_replacement_flight(
        self, carrier_codes: list[str], traveller_name: str, departure_time: str, arrival_time: str
    ) -> Dict[str, Any]:
        """Book approved replacement flight itinerary."""

    @abstractmethod
    async def cancel_missed_flight(self, booking_reference: str, reason: str) -> Dict[str, Any]:
        """Cancel missed connecting leg and initiate refund credit."""

    @abstractmethod
    async def reschedule_transfer(
        self, booking_reference: str, new_pickup_time: str
    ) -> Dict[str, Any]:
        """Update airport transfer pickup window to match new arrival."""

    @abstractmethod
    async def notify_hotel_late_checkin(
        self, booking_reference: str, expected_arrival: str
    ) -> Dict[str, Any]:
        """Guarantee room hold by updating hotel check-in expectation."""


class MockTravelProviderAdapter(TravelProviderAdapter):
    """Safe deterministic mock provider returning simulated confirmation receipts."""

    @property
    def mode(self) -> str:
        return "MOCK"

    def _confirm_code(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"

    async def book_replacement_flight(
        self, carrier_codes: list[str], traveller_name: str, departure_time: str, arrival_time: str
    ) -> Dict[str, Any]:
        pnr = self._confirm_code("MOCKPNR")
        return {
            "status": "EXECUTED",
            "adapter_mode": self.mode,
            "confirmation_code": pnr,
            "carrier_codes": carrier_codes,
            "traveller_name": traveller_name,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "message": f"[MOCK] Issued replacement e-ticket {', '.join(carrier_codes)} (PNR: {pnr}).",
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def cancel_missed_flight(self, booking_reference: str, reason: str) -> Dict[str, Any]:
        ref = self._confirm_code("MOCKCXL")
        return {
            "status": "EXECUTED",
            "adapter_mode": self.mode,
            "confirmation_code": ref,
            "cancelled_reference": booking_reference,
            "message": f"[MOCK] Cancelled missed flight {booking_reference} due to {reason}; refund queued ({ref}).",
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def reschedule_transfer(
        self, booking_reference: str, new_pickup_time: str
    ) -> Dict[str, Any]:
        ref = self._confirm_code("MOCKTRF")
        return {
            "status": "EXECUTED",
            "adapter_mode": self.mode,
            "confirmation_code": ref,
            "booking_reference": booking_reference,
            "new_pickup_time": new_pickup_time,
            "message": f"[MOCK] Rescheduled BluSmart pickup {booking_reference} to {new_pickup_time} ({ref}).",
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def notify_hotel_late_checkin(
        self, booking_reference: str, expected_arrival: str
    ) -> Dict[str, Any]:
        ref = self._confirm_code("MOCKHTL")
        return {
            "status": "EXECUTED",
            "adapter_mode": self.mode,
            "confirmation_code": ref,
            "booking_reference": booking_reference,
            "expected_arrival": expected_arrival,
            "message": f"[MOCK] Hotel {booking_reference} updated with guaranteed hold for {expected_arrival} ({ref}).",
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
