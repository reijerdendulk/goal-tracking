import re
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator


class RunWorkoutType(str, Enum):
    """Type of running workout."""

    easy = "easy"
    tempo = "tempo"
    intervals = "intervals"
    long = "long"
    race = "race"
    recovery = "recovery"


class WorkStatus(str, Enum):
    """Status of work session."""

    idea = "idea"
    todo = "todo"
    in_progress = "in_progress"
    blocked = "blocked"
    done = "done"


# ============================================
# Run Schemas
# ============================================


class RunCreate(BaseModel):
    """Schema for creating a run activity."""

    # Activity fields
    title: str = Field(..., min_length=1, max_length=500)
    notes: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    duration_min: int | None = Field(None, ge=1)
    tags: list[str] | dict[str, Any] | None = None

    # Run-specific fields
    distance_meters: int = Field(..., gt=0)
    moving_time_sec: int | None = Field(None, ge=0)
    avg_pace_sec_per_km: int | None = Field(None, ge=0)
    elevation_gain_m: int | None = Field(None, ge=0)
    rpe: int | None = Field(None, ge=1, le=10)
    workout_type: RunWorkoutType
    surface: str | None = None
    shoe: str | None = None
    splits: list[dict[str, Any]] | None = None

    @field_validator("start_at", "end_at", mode="before")
    @classmethod
    def ensure_timezone(cls, v: datetime | str | None) -> datetime | None:
        """Ensure datetime has timezone info."""
        if v is None:
            return None
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        else:
            dt = v
        if dt.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware (use UTC)")
        return dt


class RunCreateSimple(BaseModel):
    """
    iPhone-ready schema for creating a run with user-friendly inputs.

    This schema accepts human-friendly units (miles, min/mile pace) and handles
    all conversions server-side. Designed for mobile app clients.

    Timezone handling:
    - The 'date' field is interpreted as a local date in America/Los_Angeles timezone
    - Time is set to 12:00 noon local to avoid DST edge cases
    - The timestamp is then converted to UTC for storage

    Unit conversions (performed server-side):
    - distance_miles → distance_meters: multiply by 1609.344, round to int
    - pace_min_per_mile (mm:ss) → avg_pace_sec_per_km:
      1. Parse mm:ss to total seconds per mile
      2. Divide by 1.609344 to get seconds per km
      3. Round to int
    """

    # Required fields
    date: str = Field(
        ...,
        description="Run date in YYYY-MM-DD format (e.g., '2026-01-14'). "
        "Interpreted as America/Los_Angeles local date.",
        examples=["2026-01-14"],
    )
    distance_miles: float = Field(
        ...,
        gt=0,
        description="Distance in miles (e.g., 5.5 for 5.5 miles)",
        examples=[5.5, 3.1, 10.0],
    )
    pace_min_per_mile: str = Field(
        ...,
        description="Pace in mm:ss format (e.g., '8:30' for 8 minutes 30 seconds per mile)",
        examples=["8:30", "7:00", "10:15"],
    )

    # Optional fields
    notes: str | None = Field(
        None,
        description="Optional notes about the run",
        examples=["Felt great today!", "Recovery run after yesterday's tempo"],
    )
    workout_type: RunWorkoutType = Field(
        RunWorkoutType.easy,
        description="Type of workout",
    )

    @field_validator("date", mode="after")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """
        Validate date is in YYYY-MM-DD or MM/DD/YYYY format.
        Normalizes to YYYY-MM-DD for internal processing.
        """
        v = v.strip()

        # Try YYYY-MM-DD (canonical format)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            try:
                datetime.strptime(v, "%Y-%m-%d")
                return v
            except ValueError:
                raise ValueError(
                    f"Invalid date '{v}'. Must be a valid date in YYYY-MM-DD format."
                )

        # Try MM/DD/YYYY (legacy format for backward compatibility)
        if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", v):
            try:
                dt = datetime.strptime(v, "%m/%d/%Y")
                return dt.strftime("%Y-%m-%d")  # Normalize to canonical format
            except ValueError:
                raise ValueError(
                    f"Invalid date '{v}'. Must be a valid date in MM/DD/YYYY format."
                )

        raise ValueError(
            f"Invalid date format '{v}'. Use YYYY-MM-DD (preferred) or MM/DD/YYYY."
        )

    @field_validator("pace_min_per_mile", mode="after")
    @classmethod
    def validate_pace_format(cls, v: str) -> str:
        """Validate pace is in mm:ss format with seconds 00-59."""
        v = v.strip()
        if not re.match(r"^\d+:[0-5]\d$", v):
            raise ValueError(
                f"Invalid pace format '{v}'. Must be mm:ss (e.g., '8:30') "
                "with seconds between 00-59."
            )
        return v

    def to_run_create(self) -> "RunCreate":
        """
        Convert user-friendly input to internal RunCreate schema.

        Performs:
        1. Date → UTC timestamp conversion (noon in America/Los_Angeles)
        2. Miles → meters conversion
        3. Pace mm:ss → seconds per km conversion
        """
        # Parse date and convert to UTC timestamp
        # Interpret as noon in America/Los_Angeles to avoid DST issues
        local_date = datetime.strptime(self.date, "%Y-%m-%d").date()
        la_tz = ZoneInfo("America/Los_Angeles")
        local_noon = datetime(
            local_date.year, local_date.month, local_date.day, 12, 0, 0, tzinfo=la_tz
        )
        utc_timestamp = local_noon.astimezone(ZoneInfo("UTC"))

        # Convert miles to meters: 1 mile = 1609.344 meters
        distance_meters = round(self.distance_miles * 1609.344)

        # Convert pace from min/mile to sec/km
        # Formula: (minutes * 60 + seconds) / 1.609344
        parts = self.pace_min_per_mile.split(":")
        minutes = int(parts[0])
        seconds = int(parts[1])
        sec_per_mile = minutes * 60 + seconds
        avg_pace_sec_per_km = round(sec_per_mile / 1.609344)

        # Generate title from distance
        title = f"Run - {self.distance_miles} mi"

        return RunCreate(
            title=title,
            notes=self.notes,
            start_at=utc_timestamp,
            end_at=None,
            duration_min=None,
            tags=None,
            distance_meters=distance_meters,
            moving_time_sec=None,
            avg_pace_sec_per_km=avg_pace_sec_per_km,
            elevation_gain_m=None,
            rpe=None,
            workout_type=self.workout_type,
            surface=None,
            shoe=None,
            splits=None,
        )


class RunResponse(BaseModel):
    """Response schema for created run."""

    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class RunListItem(BaseModel):
    """Response schema for a run in list view."""

    id: UUID
    title: str
    notes: str | None
    start_at: datetime
    created_at: datetime
    duration_min: int | None
    distance_meters: int
    avg_pace_sec_per_km: int | None
    workout_type: str

    model_config = {"from_attributes": True}


# ============================================
# Hangout Schemas
# ============================================


class ParticipantInput(BaseModel):
    """Input for a participant - either existing (by id) or new (by name)."""

    id: UUID | None = None
    name: str | None = None
    handle: str | None = None
    role: str | None = None

    @field_validator("name", mode="after")
    @classmethod
    def validate_participant(cls, v: str | None, info) -> str | None:
        """Ensure either id or name is provided."""
        # This validator runs on name, but we check the whole model state
        return v


class HangoutCreate(BaseModel):
    """Schema for creating a hangout activity."""

    # Activity fields
    title: str = Field(..., min_length=1, max_length=500)
    notes: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    duration_min: int | None = Field(None, ge=1)
    tags: list[str] | dict[str, Any] | None = None

    # Hangout-specific fields
    location_name: str | None = None
    location_type: str | None = None
    cost_estimate: Decimal | None = Field(None, ge=0)
    mood: int | None = Field(None, ge=1, le=5)

    # Participants
    participants: list[ParticipantInput] | None = None

    @field_validator("start_at", "end_at", mode="before")
    @classmethod
    def ensure_timezone(cls, v: datetime | str | None) -> datetime | None:
        """Ensure datetime has timezone info."""
        if v is None:
            return None
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        else:
            dt = v
        if dt.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware (use UTC)")
        return dt

    @field_validator("participants", mode="after")
    @classmethod
    def validate_participants(
        cls, v: list[ParticipantInput] | None
    ) -> list[ParticipantInput] | None:
        """Validate that each participant has either id or name."""
        if v is None:
            return v
        for p in v:
            if p.id is None and p.name is None:
                raise ValueError("Each participant must have either 'id' or 'name'")
        return v


class HangoutResponse(BaseModel):
    """Response schema for created hangout."""

    id: UUID
    created_at: datetime
    participants_created: int = 0

    model_config = {"from_attributes": True}


# ============================================
# Work Session Schemas
# ============================================


class WorkSessionCreate(BaseModel):
    """Schema for creating a work session activity."""

    # Activity fields
    title: str = Field(..., min_length=1, max_length=500)
    notes: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    duration_min: int | None = Field(None, ge=1)
    tags: list[str] | dict[str, Any] | None = None

    # Work-specific fields
    project: str = Field(..., min_length=1)
    area: str | None = None
    status: WorkStatus = WorkStatus.in_progress
    artifact_link: str | None = None

    @field_validator("start_at", "end_at", mode="before")
    @classmethod
    def ensure_timezone(cls, v: datetime | str | None) -> datetime | None:
        """Ensure datetime has timezone info."""
        if v is None:
            return None
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        else:
            dt = v
        if dt.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware (use UTC)")
        return dt


class WorkSessionResponse(BaseModel):
    """Response schema for created work session."""

    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# Stats Schemas
# ============================================


class WeeklyBreakdown(BaseModel):
    """Weekly breakdown of activities."""

    week_start: str  # ISO date string (YYYY-MM-DD)
    runs_count: int = 0
    distance_meters: int = 0
    run_duration_min: int = 0
    hangouts_count: int = 0
    work_sessions_count: int = 0
    work_minutes: int = 0


class WeeklyStatsResponse(BaseModel):
    """Response schema for weekly stats."""

    # Totals
    total_runs: int = 0
    total_distance_meters: int = 0
    total_run_duration_min: int = 0
    total_hangouts: int = 0
    total_work_sessions: int = 0
    total_work_minutes: int = 0

    # Weekly breakdown
    weeks: list[WeeklyBreakdown] = []


# ============================================
# Health Schemas
# ============================================


class HealthResponse(BaseModel):
    """Response schema for health check."""

    ok: bool
    db: str
