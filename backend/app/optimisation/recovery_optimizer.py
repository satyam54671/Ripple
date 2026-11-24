"""Constraint-based recovery optimization engine powered by Google OR-Tools CP-SAT."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from ortools.sat.python import cp_model

IST = timezone(timedelta(hours=5, minutes=30))


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=IST)
    return dt

from app.schemas.trip import (
    ImpactAnalysisResult,
    NodeType,
    RecoveryActionStep,
    RecoveryOption,
    TripItinerary,
)


class RecoveryOptimizer:
    """
    Uses Google OR-Tools CP-SAT solver to evaluate and rank recovery alternatives
    against arrival deadlines, additional cost, travel policy, connection risk,
    and downstream commitment preservation.
    """

    def optimize(
        self,
        itinerary: TripItinerary,
        impact: ImpactAnalysisResult,
        candidates: List[Dict[str, Any]],
    ) -> List[RecoveryOption]:
        if not candidates:
            return []

        policy = itinerary.policy

        # Extract critical meeting hard deadline and hotel cutoff from itinerary
        meeting_node = next(
            (n for n in itinerary.nodes if n.node_type == NodeType.MEETING), None
        )
        hotel_node = next(
            (n for n in itinerary.nodes if n.node_type == NodeType.HOTEL), None
        )
        transfer_node = next(
            (n for n in itinerary.nodes if n.node_type == NodeType.TRANSFER), None
        )
        missed_flight = next(
            (
                n
                for n in itinerary.nodes
                if n.node_type == NodeType.FLIGHT and n.id != impact.root_node_id
            ),
            None,
        )

        meeting_deadline: Optional[datetime] = None
        if meeting_node:
            raw_deadline = meeting_node.metadata.get("hard_arrival_deadline")
            if raw_deadline:
                meeting_deadline = _ensure_aware(datetime.fromisoformat(raw_deadline))
            else:
                meeting_deadline = _ensure_aware(meeting_node.start_time) - timedelta(
                    minutes=policy.min_meeting_buffer_minutes
                )

        hotel_cutoff: Optional[datetime] = None
        if hotel_node:
            raw_cutoff = hotel_node.metadata.get("late_checkin_cutoff")
            if raw_cutoff:
                hotel_cutoff = _ensure_aware(datetime.fromisoformat(raw_cutoff))

        evaluated: List[Dict[str, Any]] = []

        for idx, cand in enumerate(candidates):
            dep_dt = _ensure_aware(datetime.fromisoformat(cand["departure_time"]))
            arr_dt = _ensure_aware(datetime.fromisoformat(cand["arrival_time"]))
            fare = float(cand["fare_inr"])
            refund_credit = float(cand.get("refund_credit_inr", 0.0))
            net_cost = max(0.0, fare - refund_credit)
            stops = int(cand.get("stops", 0))
            cabin = str(cand.get("cabin_class", "ECONOMY")).upper()

            constraint_notes: List[str] = []

            # 1. Arrival deadline feasibility
            meets_deadline = True
            preserves_meeting = True
            if meeting_deadline is not None and arr_dt > meeting_deadline:
                meets_deadline = False
                preserves_meeting = False
                late_mins = int((arr_dt - meeting_deadline).total_seconds() // 60)
                constraint_notes.append(
                    f"Misses arrival buffer ({meeting_deadline.strftime('%H:%M')} IST) by {late_mins}m; puts {meeting_node.title} at risk."
                )
            elif meeting_node:
                buffer_mins = int((meeting_node.start_time - arr_dt).total_seconds() // 60)
                constraint_notes.append(
                    f"Arrives {buffer_mins}m before 09:30 AM client meeting (meets {policy.min_meeting_buffer_minutes}m buffer)."
                )

            # 2. Company travel policy compliance
            is_policy_compliant = True
            if fare > policy.max_rebooking_budget_inr:
                is_policy_compliant = False
                constraint_notes.append(
                    f"Fare ₹{fare:,.0f} exceeds policy cap of ₹{policy.max_rebooking_budget_inr:,.0f}."
                )
            if cabin != policy.preferred_cabin.upper() and not policy.allow_business_upgrade_if_critical:
                is_policy_compliant = False
                constraint_notes.append(
                    f"{cabin.title()} cabin violates company {policy.preferred_cabin.title()} policy."
                )

            # 3. Hotel check-in preservation
            preserves_hotel = True
            if hotel_cutoff is not None and arr_dt > hotel_cutoff:
                preserves_hotel = False
                constraint_notes.append(
                    f"Arrives after {hotel_cutoff.strftime('%H:%M')} hotel cutoff; requires late/day-use hold notification."
                )
            elif hotel_node:
                constraint_notes.append("Arrives before 04:00 AM hotel guaranteed check-in cutoff.")

            if stops == 0:
                constraint_notes.append("Non-stop routing eliminates secondary connection risk.")
            else:
                constraint_notes.append(f"Includes {stops} stop(s), adding transfer risk.")

            # Penalty cost used in CP-SAT objective (integer scale)
            # Lower penalty = better option
            penalty = int(round(net_cost))
            penalty += stops * 2800  # Strong preference for direct non-stop flights
            if not preserves_hotel:
                penalty += 1200  # Minor penalty for needing late check-in coordination
            if not meets_deadline:
                penalty += 50000
            if not is_policy_compliant:
                penalty += 35000

            is_feasible = meets_deadline and is_policy_compliant

            evaluated.append(
                {
                    "idx": idx,
                    "cand": cand,
                    "dep_dt": dep_dt,
                    "arr_dt": arr_dt,
                    "fare": fare,
                    "net_cost": net_cost,
                    "stops": stops,
                    "meets_deadline": meets_deadline,
                    "preserves_meeting": preserves_meeting,
                    "preserves_hotel": preserves_hotel,
                    "is_policy_compliant": is_policy_compliant,
                    "is_feasible": is_feasible,
                    "penalty": penalty,
                    "constraint_notes": constraint_notes,
                }
            )

        # Solve selection problem using Google OR-Tools CP-SAT
        recommended_idx = self._solve_with_cpsat(evaluated)

        # Sort: feasible options first by lowest penalty, then infeasible options by penalty
        sorted_evals = sorted(
            evaluated,
            key=lambda e: (not e["is_feasible"], e["penalty"]),
        )

        max_penalty = max(e["penalty"] for e in sorted_evals) or 1
        min_penalty = min(e["penalty"] for e in sorted_evals)

        options: List[RecoveryOption] = []
        for rank, item in enumerate(sorted_evals, start=1):
            cand = item["cand"]
            # Normalized 0-100 score (higher is better)
            if max_penalty == min_penalty:
                norm_score = 95.0
            else:
                norm_score = round(
                    max(12.0, 98.0 - 80.0 * ((item["penalty"] - min_penalty) / (max_penalty - min_penalty))),
                    1,
                )

            actions = self._build_action_plan(
                cand=cand,
                arr_dt=item["arr_dt"],
                preserves_hotel=item["preserves_hotel"],
                preserves_meeting=item["preserves_meeting"],
                missed_flight_id=missed_flight.id if missed_flight else None,
                missed_flight_provider=missed_flight.provider if missed_flight else "Air India",
                transfer_id=transfer_node.id if transfer_node else None,
                transfer_provider=transfer_node.provider if transfer_node else "BluSmart Mobility",
                hotel_id=hotel_node.id if hotel_node else None,
                hotel_provider=hotel_node.provider if hotel_node else "The Oberoi",
                meeting_id=meeting_node.id if meeting_node else None,
            )

            options.append(
                RecoveryOption(
                    id=cand["option_id"],
                    label=cand["label"],
                    summary=(
                        f"Arrives {item['arr_dt'].strftime('%d %b %H:%M')} IST · "
                        f"Fare ₹{item['fare']:,.0f} (Net ₹{item['net_cost']:,.0f})"
                    ),
                    route_description=cand["route_description"],
                    carrier_codes=cand["carrier_codes"],
                    departure_time=item["dep_dt"],
                    arrival_time=item["arr_dt"],
                    additional_cost_inr=item["fare"],
                    net_cost_after_refund_inr=item["net_cost"],
                    stops=item["stops"],
                    preserves_meeting=item["preserves_meeting"],
                    preserves_hotel_checkin=item["preserves_hotel"],
                    is_policy_compliant=item["is_policy_compliant"],
                    meets_deadline=item["meets_deadline"],
                    optimizer_score=norm_score,
                    rank=rank,
                    is_recommended=(item["idx"] == recommended_idx),
                    inventory_mode=cand.get("inventory_mode", "MOCK_INVENTORY"),
                    constraint_notes=item["constraint_notes"],
                    actions=actions,
                )
            )

        return options

    def _solve_with_cpsat(self, evaluated: List[Dict[str, Any]]) -> int:
        """Formulate and solve the binary selection problem via OR-Tools CP-SAT."""
        model = cp_model.CpModel()
        x = [model.NewBoolVar(f"select_{i}") for i in range(len(evaluated))]

        # Exactly one recovery option must be chosen
        model.Add(sum(x) == 1)

        # Enforce hard feasibility constraints if at least one feasible candidate exists
        feasible_indices = [e["idx"] for e in evaluated if e["is_feasible"]]
        if feasible_indices:
            for e in evaluated:
                if not e["is_feasible"]:
                    model.Add(x[e["idx"]] == 0)

        # Minimize total weighted penalty
        model.Minimize(sum(x[e["idx"]] * e["penalty"] for e in evaluated))

        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for i, var in enumerate(x):
                if solver.Value(var) == 1:
                    return i
        return 0

    def _build_action_plan(
        self,
        cand: Dict[str, Any],
        arr_dt: datetime,
        preserves_hotel: bool,
        preserves_meeting: bool,
        missed_flight_id: Optional[str],
        missed_flight_provider: str,
        transfer_id: Optional[str],
        transfer_provider: str,
        hotel_id: Optional[str],
        hotel_provider: str,
        meeting_id: Optional[str],
    ) -> List[RecoveryActionStep]:
        actions: List[RecoveryActionStep] = []
        step = 1

        actions.append(
            RecoveryActionStep(
                step_order=step,
                action_type="BOOK_FLIGHT",
                target_node_id="flt_blr_bom",
                provider=" / ".join(cand["carrier_codes"]),
                description=(
                    f"Book replacement itinerary {', '.join(cand['carrier_codes'])} "
                    f"({cand['route_description']}) for ₹{cand['fare_inr']:,.0f}."
                ),
                requires_approval=True,
                estimated_cost_inr=float(cand["fare_inr"]),
                inventory_source="MOCK_INVENTORY",
            )
        )
        step += 1

        if missed_flight_id:
            actions.append(
                RecoveryActionStep(
                    step_order=step,
                    action_type="CANCEL_FLIGHT",
                    target_node_id=missed_flight_id,
                    provider=missed_flight_provider,
                    description="Cancel unreachable connecting leg AI-806 (BOM → DEL) & request waiver.",
                    requires_approval=True,
                    estimated_cost_inr=0.0,
                    inventory_source="MOCK_INVENTORY",
                )
            )
            step += 1

        if transfer_id:
            new_pickup = (arr_dt + timedelta(minutes=25)).strftime("%d %b %H:%M IST")
            actions.append(
                RecoveryActionStep(
                    step_order=step,
                    action_type="UPDATE_TRANSFER",
                    target_node_id=transfer_id,
                    provider=transfer_provider,
                    description=f"Reschedule BluSmart EV pickup at DEL T3 to {new_pickup}.",
                    requires_approval=True,
                    estimated_cost_inr=0.0,
                    inventory_source="MOCK_INVENTORY",
                )
            )
            step += 1

        if hotel_id:
            hotel_msg = (
                f"Confirm arrival at {arr_dt.strftime('%H:%M IST')} (within 04:00 AM cutoff)."
                if preserves_hotel
                else f"Update The Oberoi New Delhi for morning check-in / luggage hold at {arr_dt.strftime('%H:%M IST')}."
            )
            actions.append(
                RecoveryActionStep(
                    step_order=step,
                    action_type="NOTIFY_HOTEL",
                    target_node_id=hotel_id,
                    provider=hotel_provider,
                    description=hotel_msg,
                    requires_approval=True,
                    estimated_cost_inr=0.0,
                    inventory_source="MOCK_INVENTORY",
                )
            )
            step += 1

        if meeting_id and not preserves_meeting:
            actions.append(
                RecoveryActionStep(
                    step_order=step,
                    action_type="NOTIFY_MEETING",
                    target_node_id=meeting_id,
                    provider="Google Calendar",
                    description="Send late-arrival advisory to FinEdge Corp attendees.",
                    requires_approval=True,
                    estimated_cost_inr=0.0,
                    inventory_source="MOCK_INVENTORY",
                )
            )

        return actions
