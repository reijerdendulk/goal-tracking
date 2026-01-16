"""UI routes for data entry forms."""

import logging
from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app import conversions, crud, models, schemas
from app.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ui", tags=["UI"])
templates = Jinja2Templates(directory="templates")


def get_recent_activities(db: Session, limit: int = 10) -> dict:
    """
    Fetch recent activities by type.

    Returns:
        Dict with 'runs', 'hangouts', 'work' lists
    """
    # Recent runs
    runs_stmt = (
        select(models.Activity)
        .join(models.RunDetail)
        .where(models.Activity.type == models.ActivityType.run)
        .options(joinedload(models.Activity.run_detail))
        .order_by(models.Activity.start_at.desc())
        .limit(limit)
    )
    runs = db.execute(runs_stmt).scalars().all()

    # Recent hangouts
    hangouts_stmt = (
        select(models.Activity)
        .join(models.HangoutDetail)
        .where(models.Activity.type == models.ActivityType.hangout)
        .options(
            joinedload(models.Activity.hangout_detail),
            joinedload(models.Activity.participants).joinedload(
                models.ActivityParticipant.person
            ),
        )
        .order_by(models.Activity.start_at.desc())
        .limit(limit)
    )
    hangouts = db.execute(hangouts_stmt).scalars().all()

    # Recent work sessions
    work_stmt = (
        select(models.Activity)
        .join(models.WorkDetail)
        .where(models.Activity.type == models.ActivityType.work)
        .options(joinedload(models.Activity.work_detail))
        .order_by(models.Activity.start_at.desc())
        .limit(limit)
    )
    work_sessions = db.execute(work_stmt).scalars().all()

    return {
        "runs": runs,
        "hangouts": hangouts,
        "work": work_sessions,
    }


@router.get("/", response_class=HTMLResponse)
async def ui_home(request: Request, db: Session = Depends(get_db)):
    """UI homepage with links to forms and recent entries."""
    recent = get_recent_activities(db)
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "recent_runs": recent["runs"],
            "recent_hangouts": recent["hangouts"],
            "recent_work": recent["work"],
        },
    )


@router.get("/runs", response_class=HTMLResponse)
async def ui_runs_form(request: Request):
    """Display run entry form."""
    return templates.TemplateResponse("run_form.html", {"request": request, "error": None})


@router.post("/runs")
async def ui_create_run(
    request: Request,
    db: Session = Depends(get_db),
    date_input: str = Form(...),
    distance_miles: float = Form(...),
    pace_min_per_mile: str = Form(...),
    notes: str = Form(""),
):
    """
    Handle run form submission.

    Converts miles/min-per-mile to meters/sec-per-km and calls canonical create_run.
    """
    try:
        # Parse date and set time to 12:00 UTC (deterministic timestamp)
        run_date = datetime.strptime(date_input, "%Y-%m-%d").date()
        start_at = datetime.combine(run_date, time(12, 0), tzinfo=timezone.utc)

        # Validate distance
        if distance_miles <= 0:
            raise ValueError("Distance must be greater than 0")

        # Convert units
        distance_meters = conversions.miles_to_meters(distance_miles)
        avg_pace_sec_per_km = conversions.pace_min_per_mile_to_sec_per_km(pace_min_per_mile)

        # Create run via canonical CRUD function
        run_create = schemas.RunCreate(
            title=f"Run - {distance_miles} mi",
            notes=notes or None,
            start_at=start_at,
            end_at=None,
            duration_min=None,
            tags=None,
            distance_meters=distance_meters,
            moving_time_sec=None,
            avg_pace_sec_per_km=avg_pace_sec_per_km,
            elevation_gain_m=None,
            rpe=None,
            workout_type=schemas.RunWorkoutType.easy,  # Default to easy
            surface=None,
            shoe=None,
            splits=None,
        )

        activity = crud.create_run(db, run_create)
        logger.info(f"Created run via UI: {activity.id}")

        # PRG pattern: redirect to home
        return RedirectResponse(url="/ui", status_code=303)

    except ValueError as e:
        logger.warning(f"Validation error in run form: {e}")
        return templates.TemplateResponse(
            "run_form.html",
            {"request": request, "error": str(e)},
            status_code=400,
        )
    except Exception as e:
        logger.error(f"Failed to create run via UI: {e}")
        return templates.TemplateResponse(
            "run_form.html",
            {"request": request, "error": f"Error creating run: {str(e)}"},
            status_code=500,
        )


@router.get("/hangouts", response_class=HTMLResponse)
async def ui_hangouts_form(request: Request):
    """Display hangout entry form."""
    return templates.TemplateResponse(
        "hangout_form.html", {"request": request, "error": None}
    )


@router.post("/hangouts")
async def ui_create_hangout(
    request: Request,
    db: Session = Depends(get_db),
    title: str = Form(...),
    location_name: str = Form(""),
    location_type: str = Form(""),
    mood: str = Form(""),
    participants: str = Form(""),
    notes: str = Form(""),
):
    """
    Handle hangout form submission.

    Participants are comma-separated names that get upserted.
    """
    try:
        # Use current timestamp
        start_at = datetime.now(timezone.utc)

        # Parse mood (optional)
        mood_int = None
        if mood.strip():
            mood_int = int(mood)
            if mood_int < 1 or mood_int > 5:
                raise ValueError("Mood must be between 1 and 5")

        # Parse participants (comma-separated names)
        participant_list = None
        if participants.strip():
            names = [name.strip() for name in participants.split(",") if name.strip()]
            participant_list = [schemas.ParticipantInput(name=name) for name in names]

        # Create hangout via canonical CRUD function
        hangout_create = schemas.HangoutCreate(
            title=title,
            notes=notes or None,
            start_at=start_at,
            end_at=None,
            duration_min=None,
            tags=None,
            location_name=location_name or None,
            location_type=location_type or None,
            cost_estimate=None,
            mood=mood_int,
            participants=participant_list,
        )

        activity, participants_created = crud.create_hangout(db, hangout_create)
        logger.info(
            f"Created hangout via UI: {activity.id}, "
            f"participants created: {participants_created}"
        )

        # PRG pattern: redirect to home
        return RedirectResponse(url="/ui", status_code=303)

    except ValueError as e:
        logger.warning(f"Validation error in hangout form: {e}")
        return templates.TemplateResponse(
            "hangout_form.html",
            {"request": request, "error": str(e)},
            status_code=400,
        )
    except Exception as e:
        logger.error(f"Failed to create hangout via UI: {e}")
        return templates.TemplateResponse(
            "hangout_form.html",
            {"request": request, "error": f"Error creating hangout: {str(e)}"},
            status_code=500,
        )


@router.get("/work", response_class=HTMLResponse)
async def ui_work_form(request: Request):
    """Display work session entry form."""
    return templates.TemplateResponse(
        "work_form.html", {"request": request, "error": None}
    )


@router.post("/work")
async def ui_create_work(
    request: Request,
    db: Session = Depends(get_db),
    title: str = Form(...),
    project: str = Form("Goal Tracking"),
    area: str = Form(""),
    duration_min: str = Form(""),
    status: str = Form("in_progress"),
    artifact_link: str = Form(""),
    notes: str = Form(""),
):
    """Handle work session form submission."""
    try:
        # Use current timestamp
        start_at = datetime.now(timezone.utc)

        # Parse duration
        duration_int = None
        if duration_min.strip():
            duration_int = int(duration_min)
            if duration_int < 1:
                raise ValueError("Duration must be at least 1 minute")

        # Create work session via canonical CRUD function
        work_create = schemas.WorkSessionCreate(
            title=title,
            notes=notes or None,
            start_at=start_at,
            end_at=None,
            duration_min=duration_int,
            tags=None,
            project=project,
            area=area or None,
            status=schemas.WorkStatus(status),
            artifact_link=artifact_link or None,
        )

        activity = crud.create_work_session(db, work_create)
        logger.info(f"Created work session via UI: {activity.id}")

        # PRG pattern: redirect to home
        return RedirectResponse(url="/ui", status_code=303)

    except ValueError as e:
        logger.warning(f"Validation error in work form: {e}")
        return templates.TemplateResponse(
            "work_form.html",
            {"request": request, "error": str(e)},
            status_code=400,
        )
    except Exception as e:
        logger.error(f"Failed to create work session via UI: {e}")
        return templates.TemplateResponse(
            "work_form.html",
            {"request": request, "error": f"Error creating work session: {str(e)}"},
            status_code=500,
        )
