"""Pydantic domain schemas for RIPPLE trips, dependency graphs, disruptions, and recovery."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    FLIGHT = "FLIGHT"
    HOTEL = "HOTEL"
    TRANSFER = "TRANSFER"
    MEETING = "MEETING"


class PriorityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class BookingStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    ON_TIME = "ON_TIME"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"
    MISSED_CONNECTION = "MISSED_CONNECTION"
    AT_RISK = "AT_RISK"
    REBOOKED = "REBOOKED"
    RESCHEDULED = "RESCHEDULED"


class TripStatus(str, Enum):
    ON_TRACK = "ON_TRACK"
    DISRUPTED = "DISRUPTED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    RECOVERED = "RECOVERED"


class DependencyType(str, Enum):
    CONNECTING_FLIGHT = "CONNECTING_FLIGHT"
    AIRPORT_PICKUP = "AIRPORT_PICKUP"
    HOTEL_CHECKIN = "HOTEL_CHECKIN"
    MEETING_ATTENDANCE = "MEETING_ATTENDANCE"


class TravelPolicy(BaseModel):
    max_rebooking_budget_inr: float = 18000.0
    preferred_cabin: str = "ECONOMY"
    allow_business_upgrade_if_critical: bool = False
    min_connection_minutes: int = 60
    min_meeting_buffer_minutes: int = 45
    prioritize_client_meetings: bool = True


class FlightDetails(BaseModel):
    flight_number: str
    airline: str
    origin_airport: str
    destination_airport: str
    terminal: Optional[str] = None
    seat: Optional[str] = None
    cabin_class: str = "ECONOMY"
    pnr: str


class HotelDetails(BaseModel):
    hotel_name: str
    city: str
    address: str
    room_type: str
    late_checkin_cutoff: datetime
    cancellation_policy: str


class TransferDetails(BaseModel):
    pickup_location: str
    dropoff_location: str
    vehicle_type: str
    driver_assigned: bool = True
    grace_period_minutes: int = 45


class MeetingDetails(BaseModel):
    organizer: str
    client_company: str
    venue: str
    attendees: List[str] = Field(default_factory=list)
    is_reschedulable: bool = False
    hard_arrival_deadline: datetime


class TripNode(BaseModel):
    id: str
    node_type: NodeType
    title: str
    provider: str
    booking_reference: str
    location: str
    start_time: datetime
    end_time: datetime
    priority: PriorityLevel = PriorityLevel.HIGH
    status: BookingStatus = BookingStatus.CONFIRMED
    cost_inr: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TripEdge(BaseModel):
    source_node_id: str
    target_node_id: str
    dependency_type: DependencyType
    min_buffer_minutes: int = 30
    is_hard_dependency: bool = True
    description: str = ""


class TripItinerary(BaseModel):
    id: str
    title: str
    traveller_name: str
    traveller_email: str
    origin: str
    destination: str
    status: TripStatus = TripStatus.ON_TRACK
    policy: TravelPolicy = Field(default_factory=TravelPolicy)
    nodes: List[TripNode] = Field(default_factory=list)
    edges: List[TripEdge] = Field(default_factory=list)


class DisruptionEvent(BaseModel):
    id: str
    trip_id: str
    node_id: str
    disruption_type: Literal["CANCELLATION", "DELAY", "MISSED_CONNECTION"]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM"]
    reason: str
    source: str
    verified: bool = False
    delay_minutes: int = 0
    detected_at: datetime


class ImpactedNodeReport(BaseModel):
    node_id: str
    title: str
    node_type: NodeType
    original_start: datetime
    original_end: datetime
    impact_level: Literal["ROOT_CAUSE", "BROKEN", "AT_RISK", "NEEDS_UPDATE", "UNAFFECTED"]
    recommended_action: str
    reason: str
    slack_minutes: int
    dependency_path: List[str]


class ImpactAnalysisResult(BaseModel):
    disruption_id: str
    trip_id: str
    root_node_id: str
    impacted_nodes: List[ImpactedNodeReport]
    total_affected: int
    critical_commitments_at_risk: List[str]
    summary: str


class RecoveryActionStep(BaseModel):
    step_order: int
    action_type: Literal[
        "BOOK_FLIGHT",
        "CANCEL_FLIGHT",
        "UPDATE_TRANSFER",
        "NOTIFY_HOTEL",
        "NOTIFY_MEETING",
    ]
    target_node_id: str
    provider: str
    description: str
    requires_approval: bool = True
    estimated_cost_inr: float = 0.0
    inventory_source: Literal["MOCK_INVENTORY", "LIVE_API"] = "MOCK_INVENTORY"


class RecoveryOption(BaseModel):
    id: str
    label: str
    summary: str
    route_description: str
    carrier_codes: List[str]
    departure_time: datetime
    arrival_time: datetime
    additional_cost_inr: float
    net_cost_after_refund_inr: float
    stops: int
    preserves_meeting: bool
    preserves_hotel_checkin: bool
    is_policy_compliant: bool
    meets_deadline: bool
    optimizer_score: float
    rank: int
    is_recommended: bool = False
    inventory_mode: Literal["MOCK_INVENTORY", "LIVE_API"] = "MOCK_INVENTORY"
    constraint_notes: List[str] = Field(default_factory=list)
    actions: List[RecoveryActionStep] = Field(default_factory=list)


class ExecutionActionLog(BaseModel):
    step_order: int
    action_type: str
    provider: str
    target_node_id: str
    status: Literal["EXECUTED", "VERIFIED", "SKIPPED", "FAILED"]
    confirmation_code: str
    adapter_mode: Literal["MOCK", "LIVE"] = "MOCK"
    message: str
    executed_at: datetime


class WorkflowTraceEntry(BaseModel):
    stage: str
    agent: str
    status: Literal["COMPLETED", "WAITING_APPROVAL", "FAILED", "SKIPPED"]
    message: str
    timestamp: datetime
    details: Dict[str, Any] = Field(default_factory=dict)


class RecoveryWorkflowResponse(BaseModel):
    run_id: str
    trip_id: str
    current_stage: str
    approval_status: Literal["PENDING", "APPROVED", "REJECTED", "EXECUTED"]
    disruption: Optional[DisruptionEvent] = None
    impact_analysis: Optional[ImpactAnalysisResult] = None
    recovery_options: List[RecoveryOption] = Field(default_factory=list)
    recommended_option_id: Optional[str] = None
    selected_option_id: Optional[str] = None
    execution_logs: List[ExecutionActionLog] = Field(default_factory=list)
    verification_passed: bool = False
    verification_summary: str = ""
    workflow_trace: List[WorkflowTraceEntry] = Field(default_factory=list)


class TriggerDisruptionRequest(BaseModel):
    node_id: Optional[str] = None
    disruption_type: Literal["CANCELLATION", "DELAY"] = "CANCELLATION"
    delay_minutes: int = 0
    reason: str = "Operational crew constraint & severe weather at hub"


class ApprovalDecisionRequest(BaseModel):
    option_id: str
    decision: Literal["APPROVE", "REJECT"] = "APPROVE"
    reviewer_note: str = ""
