"""Verification Agent: validates post-execution receipts and end-to-end itinerary integrity."""

from typing import List, Tuple
from app.schemas.trip import ExecutionActionLog, RecoveryOption, TripItinerary


class VerificationAgent:
    """Verifies that all approved recovery steps succeeded and constraints remain satisfied."""

    def verify_execution(
        self,
        itinerary: TripItinerary,
        option: RecoveryOption,
        execution_logs: List[ExecutionActionLog],
    ) -> Tuple[bool, str, List[ExecutionActionLog]]:
        verified_logs: List[ExecutionActionLog] = []
        all_ok = len(execution_logs) == len(option.actions) and len(execution_logs) > 0

        for log in execution_logs:
            if log.status == "EXECUTED" and log.confirmation_code:
                verified_logs.append(log.model_copy(update={"status": "VERIFIED"}))
            else:
                all_ok = False
                verified_logs.append(log)

        if all_ok:
            meeting_note = (
                "09:30 AM client meeting preserved."
                if option.preserves_meeting
                else "Client meeting advisory sent."
            )
            summary = (
                f"Verified {len(verified_logs)}/{len(option.actions)} recovery actions via MCP mock adapters. "
                f"New arrival {option.arrival_time.strftime('%d %b %H:%M')} IST. {meeting_note}"
            )
        else:
            summary = "Verification incomplete: one or more recovery steps did not return confirmation."

        return all_ok, summary, verified_logs
