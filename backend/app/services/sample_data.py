"""Seed itineraries and realistic hackathon demo scenario data for RIPPLE."""

from datetime import datetime, timedelta, timezone
from typing import List

from app.schemas.trip import (
    BookingStatus,
    DependencyType,
    NodeType,
    PriorityLevel,
    TravelPolicy,
    TripEdge,
    TripItinerary,
    TripNode,
    TripStatus,
)

IST = timezone(timedelta(hours=5, minutes=30))


def build_blr_bom_del_demo_trip() -> TripItinerary:
    """
    Core Demo Scenario:
    Business traveller flying Bengaluru (BLR) -> Mumbai (BOM) -> Delhi (DEL),
    with airport transfer, Delhi hotel reservation, and a 09:30 AM client meeting.
    """
    return TripItinerary(
        id="trip_blr_bom_del_001",
        title="FinEdge Q4 Architecture Review — Delhi",
        traveller_name="Aarav Mehta",
        traveller_email="aarav.mehta@rippledemos.io",
        origin="BLR",
        destination="DEL",
        status=TripStatus.ON_TRACK,
        policy=TravelPolicy(
            max_rebooking_budget_inr=18000.0,
            preferred_cabin="ECONOMY",
            allow_business_upgrade_if_critical=False,
            min_connection_minutes=60,
            min_meeting_buffer_minutes=45,
            prioritize_client_meetings=True,
        ),
        nodes=[
            TripNode(
                id="flt_blr_bom",
                node_type=NodeType.FLIGHT,
                title="IndiGo 6E-512 (BLR → BOM)",
                provider="IndiGo Airlines",
                booking_reference="RPL89K",
                location="Bengaluru (BLR T1) → Mumbai (BOM T2)",
                start_time=datetime(2026, 11, 25, 20, 15, tzinfo=IST),
                end_time=datetime(2026, 11, 25, 22, 0, tzinfo=IST),
                priority=PriorityLevel.HIGH,
                status=BookingStatus.ON_TIME,
                cost_inr=5800.0,
                metadata={
                    "flight_number": "6E-512",
                    "airline": "IndiGo",
                    "origin_airport": "BLR",
                    "destination_airport": "BOM",
                    "cabin_class": "ECONOMY",
                    "seat": "14C",
                    "refundable_amount_inr": 5800.0,
                },
            ),
            TripNode(
                id="flt_bom_del",
                node_type=NodeType.FLIGHT,
                title="Air India AI-806 (BOM → DEL)",
                provider="Air India",
                booking_reference="AI442M",
                location="Mumbai (BOM T2) → New Delhi (DEL T3)",
                start_time=datetime(2026, 11, 25, 23, 15, tzinfo=IST),
                end_time=datetime(2026, 11, 26, 1, 25, tzinfo=IST),
                priority=PriorityLevel.HIGH,
                status=BookingStatus.CONFIRMED,
                cost_inr=7200.0,
                metadata={
                    "flight_number": "AI-806",
                    "airline": "Air India",
                    "origin_airport": "BOM",
                    "destination_airport": "DEL",
                    "cabin_class": "ECONOMY",
                    "seat": "9A",
                    "refundable_amount_inr": 5200.0,
                },
            ),
            TripNode(
                id="trf_del_hotel",
                node_type=NodeType.TRANSFER,
                title="BluSmart Executive Sedan (DEL T3 → Hotel)",
                provider="BluSmart Mobility",
                booking_reference="BLU-7741",
                location="IGI Airport T3 → The Oberoi, New Delhi",
                start_time=datetime(2026, 11, 26, 1, 55, tzinfo=IST),
                end_time=datetime(2026, 11, 26, 2, 40, tzinfo=IST),
                priority=PriorityLevel.MEDIUM,
                status=BookingStatus.CONFIRMED,
                cost_inr=1250.0,
                metadata={
                    "pickup_location": "DEL Terminal 3 Arrival Gate 4",
                    "dropoff_location": "The Oberoi, Dr. Zakir Hussain Marg",
                    "vehicle_type": "Executive EV Sedan",
                    "grace_period_minutes": 45,
                },
            ),
            TripNode(
                id="htl_del_oberoi",
                node_type=NodeType.HOTEL,
                title="The Oberoi, New Delhi",
                provider="Oberoi Hotels & Resorts",
                booking_reference="OBR-99210",
                location="New Delhi, India",
                start_time=datetime(2026, 11, 26, 2, 45, tzinfo=IST),
                end_time=datetime(2026, 11, 27, 12, 0, tzinfo=IST),
                priority=PriorityLevel.HIGH,
                status=BookingStatus.CONFIRMED,
                cost_inr=19500.0,
                metadata={
                    "hotel_name": "The Oberoi, New Delhi",
                    "room_type": "Premier Room",
                    "late_checkin_cutoff": "2026-11-26T04:00:00+05:30",
                    "cancellation_policy": "Free modification 24h prior; no-show hold after 04:00 AM",
                },
            ),
            TripNode(
                id="mtg_del_client",
                node_type=NodeType.MEETING,
                title="Client Meeting: FinEdge Corp Q4 Architecture Review",
                provider="Google Calendar",
                booking_reference="GCAL-FE-0930",
                location="FinEdge Corp HQ, Connaught Place, New Delhi",
                start_time=datetime(2026, 11, 26, 9, 30, tzinfo=IST),
                end_time=datetime(2026, 11, 26, 11, 0, tzinfo=IST),
                priority=PriorityLevel.CRITICAL,
                status=BookingStatus.CONFIRMED,
                cost_inr=0.0,
                metadata={
                    "client_company": "FinEdge Corp",
                    "organizer": "VP Engineering (FinEdge)",
                    "attendees": ["aarav.mehta@rippledemos.io", "cto@finedge.in", "vp.arch@finedge.in"],
                    "is_reschedulable": False,
                    "hard_arrival_deadline": "2026-11-26T08:45:00+05:30",
                },
            ),
        ],
        edges=[
            TripEdge(
                source_node_id="flt_blr_bom",
                target_node_id="flt_bom_del",
                dependency_type=DependencyType.CONNECTING_FLIGHT,
                min_buffer_minutes=60,
                is_hard_dependency=True,
                description="Must land in BOM at least 60 min before AI-806 boarding closes.",
            ),
            TripEdge(
                source_node_id="flt_bom_del",
                target_node_id="trf_del_hotel",
                dependency_type=DependencyType.AIRPORT_PICKUP,
                min_buffer_minutes=25,
                is_hard_dependency=True,
                description="BluSmart EV pickup waits up to 45 min after DEL arrival.",
            ),
            TripEdge(
                source_node_id="trf_del_hotel",
                target_node_id="htl_del_oberoi",
                dependency_type=DependencyType.HOTEL_CHECKIN,
                min_buffer_minutes=5,
                is_hard_dependency=False,
                description="Hotel guaranteed check-in holds room until 04:00 AM unless notified.",
            ),
            TripEdge(
                source_node_id="flt_bom_del",
                target_node_id="mtg_del_client",
                dependency_type=DependencyType.MEETING_ATTENDANCE,
                min_buffer_minutes=45,
                is_hard_dependency=True,
                description="Traveller must arrive in DEL by 08:45 AM to reach 09:30 AM client meeting.",
            ),
        ],
    )


def build_secondary_sample_trip() -> TripItinerary:
    """A healthy secondary trip so the dashboard displays multi-trip portfolio visibility."""
    return TripItinerary(
        id="trip_del_sin_002",
        title="APAC Partner Summit — Singapore",
        traveller_name="Priya Nair",
        traveller_email="priya.nair@rippledemos.io",
        origin="DEL",
        destination="SIN",
        status=TripStatus.ON_TRACK,
        policy=TravelPolicy(max_rebooking_budget_inr=45000.0),
        nodes=[
            TripNode(
                id="flt_del_sin",
                node_type=NodeType.FLIGHT,
                title="Singapore Airlines SQ-403 (DEL → SIN)",
                provider="Singapore Airlines",
                booking_reference="SQ901Z",
                location="New Delhi (DEL T3) → Singapore (SIN T3)",
                start_time=datetime(2026, 11, 28, 21, 50, tzinfo=IST),
                end_time=datetime(2026, 11, 29, 6, 10, tzinfo=IST),
                priority=PriorityLevel.HIGH,
                status=BookingStatus.ON_TIME,
                cost_inr=32400.0,
                metadata={
                    "flight_number": "SQ-403",
                    "origin_airport": "DEL",
                    "destination_airport": "SIN",
                },
            ),
            TripNode(
                id="htl_sin_mbs",
                node_type=NodeType.HOTEL,
                title="Marina Bay Sands",
                provider="Marina Bay Sands",
                booking_reference="MBS-4418",
                location="Singapore",
                start_time=datetime(2026, 11, 29, 14, 0, tzinfo=IST),
                end_time=datetime(2026, 12, 1, 12, 0, tzinfo=IST),
                priority=PriorityLevel.MEDIUM,
                status=BookingStatus.CONFIRMED,
                cost_inr=54000.0,
                metadata={"hotel_name": "Marina Bay Sands"},
            ),
            TripNode(
                id="mtg_sin_keynote",
                node_type=NodeType.MEETING,
                title="APAC Partner Keynote Prep",
                provider="Google Calendar",
                booking_reference="GCAL-SIN-1100",
                location="Sands Expo Convention Centre",
                start_time=datetime(2026, 11, 29, 15, 30, tzinfo=IST),
                end_time=datetime(2026, 11, 29, 17, 0, tzinfo=IST),
                priority=PriorityLevel.HIGH,
                status=BookingStatus.CONFIRMED,
                cost_inr=0.0,
                metadata={
                    "client_company": "APAC Cloud Alliance",
                    "hard_arrival_deadline": "2026-11-29T13:30:00+05:30",
                },
            ),
        ],
        edges=[
            TripEdge(
                source_node_id="flt_del_sin",
                target_node_id="htl_sin_mbs",
                dependency_type=DependencyType.HOTEL_CHECKIN,
                min_buffer_minutes=60,
                is_hard_dependency=False,
                description="Morning arrival before standard afternoon check-in.",
            ),
            TripEdge(
                source_node_id="flt_del_sin",
                target_node_id="mtg_sin_keynote",
                dependency_type=DependencyType.MEETING_ATTENDANCE,
                min_buffer_minutes=120,
                is_hard_dependency=True,
                description="Flight arrival provides 9h buffer before afternoon keynote prep.",
            ),
        ],
    )


def get_initial_sample_trips() -> List[TripItinerary]:
    return [build_blr_bom_del_demo_trip(), build_secondary_sample_trip()]
