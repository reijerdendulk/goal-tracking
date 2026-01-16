import logging
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import crud, schemas, ui_routes
from app.config import get_settings
from app.db import get_db

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Goal Tracking API",
    description="Track running, hangouts, and work sessions",
    version="1.0.0",
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include UI routes
app.include_router(ui_routes.router)


@app.get("/health", response_model=schemas.HealthResponse)
def health_check(db: Session = Depends(get_db)) -> schemas.HealthResponse:
    """
    Health check endpoint.

    Verifies database connectivity and returns status.
    """
    db_ok = crud.check_db_connection(db)
    return schemas.HealthResponse(
        ok=db_ok,
        db="ok" if db_ok else "error",
    )


@app.get(
    "/runs",
    response_model=list[schemas.RunListItem],
    tags=["runs"],
    summary="List all runs",
)
def list_runs(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of runs to return"),
    offset: int = Query(0, ge=0, description="Number of runs to skip"),
    db: Session = Depends(get_db),
) -> list[schemas.RunListItem]:
    """
    List all runs with their details.

    Returns runs ordered by start_at descending (most recent first).
    """
    logger.info(f"Listing runs: limit={limit}, offset={offset}")
    runs = crud.list_runs(db, limit=limit, offset=offset)
    return [
        schemas.RunListItem(
            id=run.id,
            title=run.title,
            notes=run.notes,
            start_at=run.start_at,
            created_at=run.created_at,
            duration_min=run.duration_min,
            distance_meters=run.run_detail.distance_meters,
            avg_pace_sec_per_km=run.run_detail.avg_pace_sec_per_km,
            workout_type=run.run_detail.workout_type.value,
        )
        for run in runs
    ]


@app.post(
    "/runs",
    response_model=schemas.RunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_run(
    run_data: schemas.RunCreate,
    db: Session = Depends(get_db),
) -> schemas.RunResponse:
    """
    Create a new running activity (internal format).

    Records a run with distance, pace, workout type, and other metrics.
    Expects pre-converted values (meters, seconds per km).

    For a simpler API with automatic unit conversions, use POST /runs/simple.
    """
    logger.info(f"Creating run: {run_data.title}")
    try:
        activity = crud.create_run(db, run_data)
        logger.info(f"Created run with id: {activity.id}")
        return schemas.RunResponse(
            id=activity.id,
            created_at=activity.created_at,
        )
    except Exception as e:
        logger.error(f"Failed to create run: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.post(
    "/runs/simple",
    response_model=schemas.RunResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["runs"],
    summary="Create run with user-friendly inputs (iPhone-ready)",
)
def create_run_simple(
    run_data: schemas.RunCreateSimple,
    db: Session = Depends(get_db),
) -> schemas.RunResponse:
    """
    Create a new running activity with user-friendly inputs.

    **This is the recommended endpoint for mobile apps (iPhone, Android).**

    Accepts human-readable units and performs all conversions server-side:
    - Distance in miles (converted to meters)
    - Pace in mm:ss min/mile format (converted to seconds/km)
    - Date in YYYY-MM-DD format (converted to UTC timestamp)

    **Example request:**
    ```json
    {
        "date": "2026-01-14",
        "distance_miles": 5.5,
        "pace_min_per_mile": "8:30",
        "notes": "Great morning run!"
    }
    ```

    **Timezone handling:**
    - Date is interpreted as local date in America/Los_Angeles
    - Time is set to 12:00 noon to avoid DST edge cases
    - Stored as UTC timestamp

    **Unit conversions:**
    - 1 mile = 1609.344 meters
    - Pace conversion: sec_per_km = (minutes * 60 + seconds) / 1.609344
    """
    logger.info(f"Creating run (simple): date={run_data.date}, distance={run_data.distance_miles}mi")
    try:
        # Convert user-friendly input to internal format
        internal_run_data = run_data.to_run_create()
        activity = crud.create_run(db, internal_run_data)
        logger.info(f"Created run with id: {activity.id}")
        return schemas.RunResponse(
            id=activity.id,
            created_at=activity.created_at,
        )
    except Exception as e:
        logger.error(f"Failed to create run: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.post(
    "/hangouts",
    response_model=schemas.HangoutResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_hangout(
    hangout_data: schemas.HangoutCreate,
    db: Session = Depends(get_db),
) -> schemas.HangoutResponse:
    """
    Create a new hangout activity.

    Records a social hangout with location, participants, and mood.
    """
    logger.info(f"Creating hangout: {hangout_data.title}")
    try:
        activity, participants_created = crud.create_hangout(db, hangout_data)
        logger.info(
            f"Created hangout with id: {activity.id}, "
            f"participants created: {participants_created}"
        )
        return schemas.HangoutResponse(
            id=activity.id,
            created_at=activity.created_at,
            participants_created=participants_created,
        )
    except ValueError as e:
        logger.error(f"Validation error creating hangout: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to create hangout: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.post(
    "/work-sessions",
    response_model=schemas.WorkSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_work_session(
    work_data: schemas.WorkSessionCreate,
    db: Session = Depends(get_db),
) -> schemas.WorkSessionResponse:
    """
    Create a new work session activity.

    Records a work session with project, area, status, and duration.
    """
    logger.info(f"Creating work session: {work_data.title}")
    try:
        activity = crud.create_work_session(db, work_data)
        logger.info(f"Created work session with id: {activity.id}")
        return schemas.WorkSessionResponse(
            id=activity.id,
            created_at=activity.created_at,
        )
    except Exception as e:
        logger.error(f"Failed to create work session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.get("/stats/weekly", response_model=schemas.WeeklyStatsResponse)
def get_weekly_stats(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> schemas.WeeklyStatsResponse:
    """
    Get weekly statistics for activities.

    Returns totals and weekly breakdown for runs, hangouts, and work sessions.
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date",
        )

    logger.info(f"Getting weekly stats from {start_date} to {end_date}")
    return crud.get_weekly_stats(db, start_date, end_date)


@app.get("/activity/recent")
def get_recent_activities(
    limit: int = Query(10, ge=1, le=100, description="Number of activities to return"),
    db: Session = Depends(get_db),
):
    """
    Get recent activities across all types.

    Returns the most recent activities ordered by creation date.
    """
    logger.info(f"Getting recent {limit} activities")
    activities = crud.get_recent_activities(db, limit=limit)

    # Convert to dict for JSON serialization with relationships
    result = []
    for activity in activities:
        activity_dict = {
            "id": str(activity.id),
            "type": activity.type.value,
            "title": activity.title,
            "start_at": activity.start_at.isoformat(),
            "created_at": activity.created_at.isoformat(),
            "duration_min": activity.duration_min,
        }

        # Add type-specific details
        if activity.run_detail:
            activity_dict["run_detail"] = {
                "distance_meters": activity.run_detail.distance_meters,
                "avg_pace_sec_per_km": activity.run_detail.avg_pace_sec_per_km,
            }
        if activity.hangout_detail:
            activity_dict["hangout_detail"] = {
                "mood": activity.hangout_detail.mood,
            }
        if activity.work_detail:
            activity_dict["work_detail"] = {
                "project": activity.work_detail.project,
                "status": activity.work_detail.status.value,
            }

        # Add participants
        if activity.participants:
            activity_dict["participants"] = [
                {"person": {"name": p.person.name}} for p in activity.participants
            ]

        result.append(activity_dict)

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.app_env == "local",
    )
