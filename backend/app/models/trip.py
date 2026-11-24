"""SQLAlchemy ORM models for trips, dependency graph nodes/edges, and recovery runs."""

from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TripORM(Base):
    """Persistent trip itinerary record."""

    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    traveller_name: Mapped[str] = mapped_column(String(120))
    traveller_email: Mapped[str] = mapped_column(String(160))
    origin: Mapped[str] = mapped_column(String(16))
    destination: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(32), default="ON_TRACK")
    policy_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    nodes: Mapped[list["TripNodeORM"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan"
    )
    edges: Mapped[list["TripEdgeORM"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan"
    )
    workflow_runs: Mapped[list["RecoveryWorkflowRunORM"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan"
    )


class TripNodeORM(Base):
    """Unified booking/commitment node inside a trip itinerary."""

    __tablename__ = "trip_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    node_type: Mapped[str] = mapped_column(String(32))  # FLIGHT | HOTEL | TRANSFER | MEETING
    title: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str] = mapped_column(String(120))
    booking_reference: Mapped[str] = mapped_column(String(64), default="")
    location: Mapped[str] = mapped_column(String(120))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    priority: Mapped[str] = mapped_column(String(24), default="HIGH")
    status: Mapped[str] = mapped_column(String(32), default="CONFIRMED")
    cost_inr: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    trip: Mapped["TripORM"] = relationship(back_populates="nodes")


class TripEdgeORM(Base):
    """Directed dependency edge between two trip nodes."""

    __tablename__ = "trip_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    source_node_id: Mapped[str] = mapped_column(String(64))
    target_node_id: Mapped[str] = mapped_column(String(64))
    dependency_type: Mapped[str] = mapped_column(String(48))
    min_buffer_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_hard_dependency: Mapped[bool] = mapped_column(default=True)
    description: Mapped[str] = mapped_column(Text, default="")

    trip: Mapped["TripORM"] = relationship(back_populates="edges")


class RecoveryWorkflowRunORM(Base):
    """Persisted state snapshot of a LangGraph disruption recovery run."""

    __tablename__ = "recovery_workflow_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    disrupted_node_id: Mapped[str] = mapped_column(String(64))
    current_stage: Mapped[str] = mapped_column(String(64), default="START")
    approval_status: Mapped[str] = mapped_column(String(32), default="PENDING")
    selected_option_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    trip: Mapped["TripORM"] = relationship(back_populates="workflow_runs")
