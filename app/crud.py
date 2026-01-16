from collections import defaultdict
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.utils import compute_duration_min, format_week_start, get_week_start


def create_run(db: Session, run_data: schemas.RunCreate) -> models.Activity:
    """
    Create a new run activity with run details.

    Args:
        db: Database session
        run_data: Run creation data

    Returns:
        Created Activity object
    """
    # Compute duration if not provided but end_at is
    duration_min = run_data.duration_min
    if duration_min is None and run_data.end_at is not None:
        duration_min = compute_duration_min(run_data.start_at, run_data.end_at)

    # Create activity
    activity = models.Activity(
        type=models.ActivityType.run,
        title=run_data.title,
        notes=run_data.notes,
        start_at=run_data.start_at,
        end_at=run_data.end_at,
        duration_min=duration_min,
        tags=run_data.tags,
    )
    db.add(activity)
    db.flush()  # Get the activity ID

    # Create run detail
    run_detail = models.RunDetail(
        activity_id=activity.id,
        distance_meters=run_data.distance_meters,
        moving_time_sec=run_data.moving_time_sec,
        avg_pace_sec_per_km=run_data.avg_pace_sec_per_km,
        elevation_gain_m=run_data.elevation_gain_m,
        rpe=run_data.rpe,
        workout_type=models.RunWorkoutType(run_data.workout_type.value),
        surface=run_data.surface,
        shoe=run_data.shoe,
        splits=run_data.splits,
    )
    db.add(run_detail)
    db.commit()
    db.refresh(activity)

    return activity


def get_or_create_person(
    db: Session, name: str, handle: str | None = None
) -> tuple[models.Person, bool]:
    """
    Get an existing person by name or create a new one.

    Args:
        db: Database session
        name: Person's name
        handle: Optional handle

    Returns:
        Tuple of (Person object, created: bool)
    """
    # Try to find existing person by name
    stmt = select(models.Person).where(models.Person.name == name)
    person = db.execute(stmt).scalar_one_or_none()

    if person is not None:
        return person, False

    # Create new person
    person = models.Person(name=name, handle=handle)
    db.add(person)
    db.flush()
    return person, True


def get_person_by_id(db: Session, person_id: UUID) -> models.Person | None:
    """Get a person by ID."""
    return db.get(models.Person, person_id)


def create_hangout(
    db: Session, hangout_data: schemas.HangoutCreate
) -> tuple[models.Activity, int]:
    """
    Create a new hangout activity with details and participants.

    Args:
        db: Database session
        hangout_data: Hangout creation data

    Returns:
        Tuple of (Created Activity object, number of participants created)
    """
    # Compute duration if not provided but end_at is
    duration_min = hangout_data.duration_min
    if duration_min is None and hangout_data.end_at is not None:
        duration_min = compute_duration_min(hangout_data.start_at, hangout_data.end_at)

    # Create activity
    activity = models.Activity(
        type=models.ActivityType.hangout,
        title=hangout_data.title,
        notes=hangout_data.notes,
        start_at=hangout_data.start_at,
        end_at=hangout_data.end_at,
        duration_min=duration_min,
        tags=hangout_data.tags,
    )
    db.add(activity)
    db.flush()

    # Create hangout detail
    hangout_detail = models.HangoutDetail(
        activity_id=activity.id,
        location_name=hangout_data.location_name,
        location_type=hangout_data.location_type,
        cost_estimate=hangout_data.cost_estimate,
        mood=hangout_data.mood,
    )
    db.add(hangout_detail)

    # Process participants
    participants_created = 0
    if hangout_data.participants:
        for p in hangout_data.participants:
            person: models.Person | None = None
            created = False

            if p.id is not None:
                # Use existing person by ID
                person = get_person_by_id(db, p.id)
                if person is None:
                    raise ValueError(f"Person with id {p.id} not found")
            elif p.name is not None:
                # Get or create by name
                person, created = get_or_create_person(db, p.name, p.handle)
                if created:
                    participants_created += 1

            if person is not None:
                # Create participant link
                participant = models.ActivityParticipant(
                    activity_id=activity.id,
                    person_id=person.id,
                    role=p.role,
                )
                db.add(participant)

    db.commit()
    db.refresh(activity)

    return activity, participants_created


def create_work_session(
    db: Session, work_data: schemas.WorkSessionCreate
) -> models.Activity:
    """
    Create a new work session activity with work details.

    Args:
        db: Database session
        work_data: Work session creation data

    Returns:
        Created Activity object
    """
    # Compute duration if not provided but end_at is
    duration_min = work_data.duration_min
    if duration_min is None and work_data.end_at is not None:
        duration_min = compute_duration_min(work_data.start_at, work_data.end_at)

    # Create activity
    activity = models.Activity(
        type=models.ActivityType.work,
        title=work_data.title,
        notes=work_data.notes,
        start_at=work_data.start_at,
        end_at=work_data.end_at,
        duration_min=duration_min,
        tags=work_data.tags,
    )
    db.add(activity)
    db.flush()

    # Create work detail
    work_detail = models.WorkDetail(
        activity_id=activity.id,
        project=work_data.project,
        area=work_data.area,
        status=models.WorkStatus(work_data.status.value),
        artifact_link=work_data.artifact_link,
    )
    db.add(work_detail)
    db.commit()
    db.refresh(activity)

    return activity


def get_weekly_stats(
    db: Session, start_date: date, end_date: date
) -> schemas.WeeklyStatsResponse:
    """
    Get weekly statistics for activities within a date range.

    Uses SQL aggregates grouped by week (date_trunc('week', start_at)).

    Args:
        db: Database session
        start_date: Start of date range
        end_date: End of date range

    Returns:
        WeeklyStatsResponse with totals and weekly breakdown
    """
    # Convert dates to timezone-aware datetimes
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

    # Query for runs with weekly grouping
    runs_query = text("""
        SELECT
            date_trunc('week', a.start_at) as week_start,
            COUNT(*) as count,
            COALESCE(SUM(rd.distance_meters), 0) as total_distance,
            COALESCE(SUM(a.duration_min), 0) as total_duration
        FROM activity a
        JOIN run_detail rd ON rd.activity_id = a.id
        WHERE a.type = 'run'
          AND a.start_at >= :start_dt
          AND a.start_at <= :end_dt
        GROUP BY date_trunc('week', a.start_at)
        ORDER BY week_start
    """)

    runs_result = db.execute(
        runs_query, {"start_dt": start_dt, "end_dt": end_dt}
    ).fetchall()

    # Query for hangouts with weekly grouping
    hangouts_query = text("""
        SELECT
            date_trunc('week', a.start_at) as week_start,
            COUNT(*) as count
        FROM activity a
        WHERE a.type = 'hangout'
          AND a.start_at >= :start_dt
          AND a.start_at <= :end_dt
        GROUP BY date_trunc('week', a.start_at)
        ORDER BY week_start
    """)

    hangouts_result = db.execute(
        hangouts_query, {"start_dt": start_dt, "end_dt": end_dt}
    ).fetchall()

    # Query for work sessions with weekly grouping
    work_query = text("""
        SELECT
            date_trunc('week', a.start_at) as week_start,
            COUNT(*) as count,
            COALESCE(SUM(a.duration_min), 0) as total_duration
        FROM activity a
        WHERE a.type = 'work'
          AND a.start_at >= :start_dt
          AND a.start_at <= :end_dt
        GROUP BY date_trunc('week', a.start_at)
        ORDER BY week_start
    """)

    work_result = db.execute(
        work_query, {"start_dt": start_dt, "end_dt": end_dt}
    ).fetchall()

    # Aggregate by week
    weeks_data: dict[str, schemas.WeeklyBreakdown] = defaultdict(
        lambda: schemas.WeeklyBreakdown(week_start="")
    )

    # Process runs
    total_runs = 0
    total_distance = 0
    total_run_duration = 0

    for row in runs_result:
        week_key = format_week_start(row.week_start)
        weeks_data[week_key].week_start = week_key
        weeks_data[week_key].runs_count = int(row.count)
        weeks_data[week_key].distance_meters = int(row.total_distance)
        weeks_data[week_key].run_duration_min = int(row.total_duration)

        total_runs += int(row.count)
        total_distance += int(row.total_distance)
        total_run_duration += int(row.total_duration)

    # Process hangouts
    total_hangouts = 0

    for row in hangouts_result:
        week_key = format_week_start(row.week_start)
        weeks_data[week_key].week_start = week_key
        weeks_data[week_key].hangouts_count = int(row.count)

        total_hangouts += int(row.count)

    # Process work sessions
    total_work_sessions = 0
    total_work_minutes = 0

    for row in work_result:
        week_key = format_week_start(row.week_start)
        weeks_data[week_key].week_start = week_key
        weeks_data[week_key].work_sessions_count = int(row.count)
        weeks_data[week_key].work_minutes = int(row.total_duration)

        total_work_sessions += int(row.count)
        total_work_minutes += int(row.total_duration)

    # Sort weeks and convert to list
    sorted_weeks = sorted(weeks_data.values(), key=lambda w: w.week_start)

    return schemas.WeeklyStatsResponse(
        total_runs=total_runs,
        total_distance_meters=total_distance,
        total_run_duration_min=total_run_duration,
        total_hangouts=total_hangouts,
        total_work_sessions=total_work_sessions,
        total_work_minutes=total_work_minutes,
        weeks=sorted_weeks,
    )


def get_recent_activities(db: Session, limit: int = 10) -> list[models.Activity]:
    """
    Get recent activities across all types.

    Args:
        db: Database session
        limit: Maximum number of activities to return

    Returns:
        List of Activity objects with eager-loaded relationships
    """
    stmt = (
        select(models.Activity)
        .options(
            joinedload(models.Activity.run_detail),
            joinedload(models.Activity.hangout_detail),
            joinedload(models.Activity.work_detail),
            joinedload(models.Activity.participants).joinedload(
                models.ActivityParticipant.person
            ),
        )
        .order_by(models.Activity.created_at.desc())
        .limit(limit)
    )

    return list(db.execute(stmt).scalars().unique().all())


def list_runs(db: Session, limit: int = 100, offset: int = 0) -> list[models.Activity]:
    """
    List all run activities with their details.

    Args:
        db: Database session
        limit: Maximum number of runs to return
        offset: Number of runs to skip

    Returns:
        List of Activity objects with run_detail loaded
    """
    stmt = (
        select(models.Activity)
        .where(models.Activity.type == models.ActivityType.run)
        .options(joinedload(models.Activity.run_detail))
        .order_by(models.Activity.start_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().unique().all())


def check_db_connection(db: Session) -> bool:
    """
    Check if database connection is healthy.

    Args:
        db: Database session

    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
