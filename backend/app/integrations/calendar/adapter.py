"""Google Calendar integration interface and mock adapter for traveller commitments."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class GoogleCalendarAdapter(ABC):
    """Contract for retrieving and updating calendar commitments."""

    @property
    @abstractmethod
    def mode(self) -> str:
        """Returns 'MOCK' or 'LIVE'."""

    @abstractmethod
    async def list_upcoming_commitments(
        self, traveller_email: str, trip_id: str
    ) -> List[Dict[str, Any]]:
        """Return calendar events relevant to the active travel window."""

    @abstractmethod
    async def send_meeting_advisory(
        self, event_id: str, message: str
    ) -> Dict[str, Any]:
        """Notify meeting attendees or update status notes (only if requested)."""


class MockGoogleCalendarAdapter(GoogleCalendarAdapter):
    """Mock Google Calendar adapter for the New Delhi 09:30 AM client meeting."""

    @property
    def mode(self) -> str:
        return "MOCK"

    async def list_upcoming_commitments(
        self, traveller_email: str, trip_id: str
    ) -> List[Dict[str, Any]]:
        return [
            {
                "event_id": "GCAL-FE-0930",
                "trip_id": trip_id,
                "title": "Client Meeting: FinEdge Corp Q4 Architecture Review",
                "start_time": "2026-11-26T09:30:00+05:30",
                "end_time": "2026-11-26T11:00:00+05:30",
                "location": "FinEdge Corp HQ, Connaught Place, New Delhi",
                "organizer": "vp.arch@finedge.in",
                "attendees": [traveller_email, "cto@finedge.in", "vp.arch@finedge.in"],
                "priority": "CRITICAL",
                "is_reschedulable": False,
                "hard_arrival_deadline": "2026-11-26T08:45:00+05:30",
                "adapter_mode": self.mode,
            }
        ]

    async def send_meeting_advisory(self, event_id: str, message: str) -> Dict[str, Any]:
        return {
            "event_id": event_id,
            "status": "ADVISORY_LOGGED",
            "adapter_mode": self.mode,
            "message": message,
        }
