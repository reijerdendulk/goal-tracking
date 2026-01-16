import enum
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class ActivityType(str, enum.Enum):
    """Type of activity."""

    run = "run"
    hangout = "hangout"
    work = "work"


class RunWorkoutType(str, enum.Enum):
    """Type of running workout."""

    easy = "easy"
    tempo = "tempo"
    intervals = "intervals"
    long = "long"
    race = "race"
    recovery = "recovery"


class WorkStatus(str, enum.Enum):
    """Status of work session."""

    idea = "idea"
    todo = "todo"
    in_progress = "in_progress"
    blocked = "blocked"
    done = "done"


class Activity(Base):
    """Base activity table for all activity types."""

    __tablename__ = "activity"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType, name="activity_type", create_type=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
    end_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    duration_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationships
    run_detail: Mapped["RunDetail | None"] = relationship(
        "RunDetail",
        back_populates="activity",
        uselist=False,
        cascade="all, delete-orphan",
    )
    hangout_detail: Mapped["HangoutDetail | None"] = relationship(
        "HangoutDetail",
        back_populates="activity",
        uselist=False,
        cascade="all, delete-orphan",
    )
    work_detail: Mapped["WorkDetail | None"] = relationship(
        "WorkDetail",
        back_populates="activity",
        uselist=False,
        cascade="all, delete-orphan",
    )
    participants: Mapped[list["ActivityParticipant"]] = relationship(
        "ActivityParticipant",
        back_populates="activity",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_activity_type_start_at", "type", "start_at"),
        Index("idx_activity_start_at", "start_at"),
    )


class RunDetail(Base):
    """Details specific to running activities."""

    __tablename__ = "run_detail"

    activity_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("activity.id", ondelete="CASCADE"),
        primary_key=True,
    )
    distance_meters: Mapped[int] = mapped_column(Integer, nullable=False)
    moving_time_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_pace_sec_per_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    elevation_gain_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rpe: Mapped[int | None] = mapped_column(Integer, nullable=True)
    workout_type: Mapped[RunWorkoutType] = mapped_column(
        Enum(RunWorkoutType, name="run_workout_type", create_type=False),
        nullable=False,
    )
    surface: Mapped[str | None] = mapped_column(Text, nullable=True)
    shoe: Mapped[str | None] = mapped_column(Text, nullable=True)
    splits: Mapped[Any | None] = mapped_column(JSONB, nullable=True)

    # Relationship
    activity: Mapped["Activity"] = relationship("Activity", back_populates="run_detail")

    __table_args__ = (
        CheckConstraint("distance_meters > 0", name="check_distance_positive"),
        CheckConstraint("rpe BETWEEN 1 AND 10", name="check_rpe_range"),
        Index("idx_run_detail_workout_type", "workout_type"),
        Index("idx_run_detail_distance_meters", "distance_meters"),
    )


class HangoutDetail(Base):
    """Details specific to hangout activities."""

    __tablename__ = "hangout_detail"

    activity_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("activity.id", ondelete="CASCADE"),
        primary_key=True,
    )
    location_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_estimate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    mood: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationship
    activity: Mapped["Activity"] = relationship(
        "Activity",
        back_populates="hangout_detail",
    )

    __table_args__ = (
        CheckConstraint("mood BETWEEN 1 AND 5", name="check_mood_range"),
    )


class Person(Base):
    """People who can participate in activities."""

    __tablename__ = "person"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    handle: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationships
    participations: Mapped[list["ActivityParticipant"]] = relationship(
        "ActivityParticipant",
        back_populates="person",
        cascade="all, delete-orphan",
    )


class ActivityParticipant(Base):
    """Many-to-many relationship between activities and people."""

    __tablename__ = "activity_participant"

    activity_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("activity.id", ondelete="CASCADE"),
        primary_key=True,
    )
    person_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("person.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    activity: Mapped["Activity"] = relationship(
        "Activity",
        back_populates="participants",
    )
    person: Mapped["Person"] = relationship(
        "Person",
        back_populates="participations",
    )

    __table_args__ = (
        Index("idx_activity_participant_person_activity", "person_id", "activity_id"),
    )


class WorkDetail(Base):
    """Details specific to work session activities."""

    __tablename__ = "work_detail"

    activity_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("activity.id", ondelete="CASCADE"),
        primary_key=True,
    )
    project: Mapped[str] = mapped_column(Text, nullable=False)
    area: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[WorkStatus] = mapped_column(
        Enum(WorkStatus, name="work_status", create_type=False),
        nullable=False,
        server_default=text("'in_progress'"),
    )
    artifact_link: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    activity: Mapped["Activity"] = relationship(
        "Activity",
        back_populates="work_detail",
    )

    __table_args__ = (Index("idx_work_detail_project", "project"),)
