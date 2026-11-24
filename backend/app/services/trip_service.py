"""Trip persistence and seeding service bridging SQLAlchemy ORM and Pydantic models."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

IST = timezone(timedelta(hours=5, minutes=30))


def _aware(dt: datetime) -> datetime:
    """SQLite strips tzinfo on read; normalize naive datetimes back to UTC/IST."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).astimezone(IST)
    return dt.astimezone(IST)

from app.models.trip import RecoveryWorkflowRunORM, TripEdgeORM, TripNodeORM, TripORM
from app.schemas.trip import (
    BookingStatus,
    DependencyType,
    NodeType,
    PriorityLevel,
    RecoveryWorkflowResponse,
    TravelPolicy,
    TripEdge,
    TripItinerary,
    TripNode,
    TripStatus,
)
from app.services.sample_data import build_blr_bom_del_demo_trip, get_initial_sample_trips


def orm_to_itinerary(trip_orm: TripORM) -> TripItinerary:
    nodes = [
        TripNode(
            id=n.id,
            node_type=NodeType(n.node_type),
            title=n.title,
            provider=n.provider,
            booking_reference=n.booking_reference,
            location=n.location,
            start_time=_aware(n.start_time),
            end_time=_aware(n.end_time),
            priority=PriorityLevel(n.priority),
            status=BookingStatus(n.status),
            cost_inr=n.cost_inr,
            metadata=n.metadata_json or {},
        )
        for n in sorted(trip_orm.nodes, key=lambda x: x.start_time)
    ]
    edges = [
        TripEdge(
            source_node_id=e.source_node_id,
            target_node_id=e.target_node_id,
            dependency_type=DependencyType(e.dependency_type),
            min_buffer_minutes=e.min_buffer_minutes,
            is_hard_dependency=e.is_hard_dependency,
            description=e.description,
        )
        for e in trip_orm.edges
    ]
    return TripItinerary(
        id=trip_orm.id,
        title=trip_orm.title,
        traveller_name=trip_orm.traveller_name,
        traveller_email=trip_orm.traveller_email,
        origin=trip_orm.origin,
        destination=trip_orm.destination,
        status=TripStatus(trip_orm.status),
        policy=TravelPolicy(**(trip_orm.policy_json or {})),
        nodes=nodes,
        edges=edges,
    )


def save_itinerary(db: Session, itinerary: TripItinerary) -> TripORM:
    """Upsert a TripItinerary and its nodes/edges into the database."""
    existing = db.query(TripORM).filter(TripORM.id == itinerary.id).first()
    if existing:
        db.delete(existing)
        db.flush()

    trip_orm = TripORM(
        id=itinerary.id,
        title=itinerary.title,
        traveller_name=itinerary.traveller_name,
        traveller_email=itinerary.traveller_email,
        origin=itinerary.origin,
        destination=itinerary.destination,
        status=itinerary.status.value,
        policy_json=itinerary.policy.model_dump(mode="json"),
    )
    for node in itinerary.nodes:
        trip_orm.nodes.append(
            TripNodeORM(
                id=node.id,
                trip_id=itinerary.id,
                node_type=node.node_type.value,
                title=node.title,
                provider=node.provider,
                booking_reference=node.booking_reference,
                location=node.location,
                start_time=node.start_time,
                end_time=node.end_time,
                priority=node.priority.value,
                status=node.status.value,
                cost_inr=node.cost_inr,
                metadata_json=node.metadata,
            )
        )
    for edge in itinerary.edges:
        trip_orm.edges.append(
            TripEdgeORM(
                trip_id=itinerary.id,
                source_node_id=edge.source_node_id,
                target_node_id=edge.target_node_id,
                dependency_type=edge.dependency_type.value,
                min_buffer_minutes=edge.min_buffer_minutes,
                is_hard_dependency=edge.is_hard_dependency,
                description=edge.description,
            )
        )
    db.add(trip_orm)
    db.commit()
    db.refresh(trip_orm)
    return trip_orm


def seed_initial_trips_if_empty(db: Session) -> None:
    """Seed initial demo trips once on startup when database is empty."""
    count = db.query(TripORM).count()
    if count == 0:
        for trip in get_initial_sample_trips():
            save_itinerary(db, trip)


def list_trips(db: Session) -> List[TripItinerary]:
    trips = db.query(TripORM).order_by(TripORM.created_at.asc()).all()
    return [orm_to_itinerary(t) for t in trips]


def get_trip(db: Session, trip_id: str) -> Optional[TripItinerary]:
    trip = db.query(TripORM).filter(TripORM.id == trip_id).first()
    return orm_to_itinerary(trip) if trip else None


def reset_demo_trip(db: Session) -> TripItinerary:
    """Reset the primary BLR -> BOM -> DEL demo trip and clear its workflow runs."""
    demo_trip = build_blr_bom_del_demo_trip()
    db.query(RecoveryWorkflowRunORM).filter(
        RecoveryWorkflowRunORM.trip_id == demo_trip.id
    ).delete()
    db.commit()
    trip_orm = save_itinerary(db, demo_trip)
    return orm_to_itinerary(trip_orm)


def save_workflow_run(db: Session, response: RecoveryWorkflowResponse) -> None:
    """Persist or update a recovery workflow run snapshot."""
    existing = (
        db.query(RecoveryWorkflowRunORM)
        .filter(RecoveryWorkflowRunORM.id == response.run_id)
        .first()
    )
    payload = response.model_dump(mode="json")
    if existing:
        existing.current_stage = response.current_stage
        existing.approval_status = response.approval_status
        existing.selected_option_id = response.selected_option_id
        existing.state_json = payload
    else:
        run_orm = RecoveryWorkflowRunORM(
            id=response.run_id,
            trip_id=response.trip_id,
            disrupted_node_id=response.disruption.node_id if response.disruption else "",
            current_stage=response.current_stage,
            approval_status=response.approval_status,
            selected_option_id=response.selected_option_id,
            state_json=payload,
        )
        db.add(run_orm)
    db.commit()


def get_latest_workflow_run(
    db: Session, trip_id: str
) -> Optional[RecoveryWorkflowResponse]:
    run_orm = (
        db.query(RecoveryWorkflowRunORM)
        .filter(RecoveryWorkflowRunORM.trip_id == trip_id)
        .order_by(RecoveryWorkflowRunORM.created_at.desc())
        .first()
    )
    if not run_orm:
        return None
    return RecoveryWorkflowResponse(**run_orm.state_json)


def get_workflow_run_by_id(
    db: Session, run_id: str
) -> Optional[RecoveryWorkflowResponse]:
    run_orm = (
        db.query(RecoveryWorkflowRunORM)
        .filter(RecoveryWorkflowRunORM.id == run_id)
        .first()
    )
    if not run_orm:
        return None
    return RecoveryWorkflowResponse(**run_orm.state_json)
