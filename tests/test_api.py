from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Activity, ActivityParticipant, HangoutDetail, Person, RunDetail


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_ok(self, client: TestClient):
        """Test that health check returns ok status."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["ok"] is True
        assert data["db"] == "ok"


class TestRunsEndpoint:
    """Tests for the /runs endpoint."""

    def test_create_run_success(self, client: TestClient, db_session: Session):
        """Test creating a run creates activity and run_detail rows."""
        run_data = {
            "title": "Morning tempo run",
            "notes": "Felt great!",
            "start_at": "2024-01-15T07:00:00+00:00",
            "end_at": "2024-01-15T07:45:00+00:00",
            "distance_meters": 10000,
            "moving_time_sec": 2700,
            "elevation_gain_m": 50,
            "rpe": 7,
            "workout_type": "tempo",
            "surface": "road",
            "shoe": "Nike Pegasus",
            "tags": ["morning", "tempo"],
        }

        response = client.post("/runs", json=run_data)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert "created_at" in data

        # Verify activity was created
        activity = db_session.get(Activity, data["id"])
        assert activity is not None
        assert activity.title == "Morning tempo run"
        assert activity.type.value == "run"
        assert activity.duration_min == 45  # Computed from start/end

        # Verify run_detail was created
        run_detail = db_session.get(RunDetail, data["id"])
        assert run_detail is not None
        assert run_detail.distance_meters == 10000
        assert run_detail.workout_type.value == "tempo"
        assert run_detail.rpe == 7

    def test_create_run_with_manual_duration(
        self, client: TestClient, db_session: Session
    ):
        """Test creating a run with manual duration (no end_at)."""
        run_data = {
            "title": "Quick run",
            "start_at": "2024-01-15T12:00:00+00:00",
            "duration_min": 30,
            "distance_meters": 5000,
            "workout_type": "easy",
        }

        response = client.post("/runs", json=run_data)
        assert response.status_code == 201

        activity = db_session.get(Activity, response.json()["id"])
        assert activity.duration_min == 30
        assert activity.end_at is None

    def test_create_run_validation_error(self, client: TestClient):
        """Test that invalid run data returns validation error."""
        run_data = {
            "title": "Bad run",
            "start_at": "2024-01-15T07:00:00+00:00",
            "distance_meters": -100,  # Invalid: must be positive
            "workout_type": "easy",
        }

        response = client.post("/runs", json=run_data)
        assert response.status_code == 422


class TestRunsSimpleEndpoint:
    """Tests for the /runs/simple endpoint (iPhone-ready API)."""

    def test_create_run_simple_canonical_date(
        self, client: TestClient, db_session: Session
    ):
        """Test creating a run with YYYY-MM-DD date format (canonical)."""
        run_data = {
            "date": "2026-01-14",
            "distance_miles": 5.5,
            "pace_min_per_mile": "8:30",
            "notes": "Great morning run!",
        }

        response = client.post("/runs/simple", json=run_data)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert "created_at" in data

        # Verify activity was created with correct conversions
        activity = db_session.get(Activity, data["id"])
        assert activity is not None
        assert activity.title == "Run - 5.5 mi"
        assert activity.type.value == "run"
        assert activity.notes == "Great morning run!"

        # Verify run_detail was created with correct unit conversions
        run_detail = db_session.get(RunDetail, data["id"])
        assert run_detail is not None
        # 5.5 miles * 1609.344 = 8851.392 → 8851 meters
        assert run_detail.distance_meters == 8851
        # 8:30 min/mile = 510 sec/mile / 1.609344 = 316.89 → 317 sec/km
        assert run_detail.avg_pace_sec_per_km == 317
        assert run_detail.workout_type.value == "easy"

    def test_create_run_simple_legacy_date_format(
        self, client: TestClient, db_session: Session
    ):
        """Test creating a run with MM/DD/YYYY date format (backward compatibility)."""
        run_data = {
            "date": "01/14/2026",
            "distance_miles": 3.1,
            "pace_min_per_mile": "7:00",
        }

        response = client.post("/runs/simple", json=run_data)
        assert response.status_code == 201

        activity = db_session.get(Activity, response.json()["id"])
        assert activity is not None
        # Should have normalized to correct date
        assert "2026" in str(activity.start_at)

    def test_create_run_simple_with_workout_type(
        self, client: TestClient, db_session: Session
    ):
        """Test creating a run with explicit workout type."""
        run_data = {
            "date": "2026-01-14",
            "distance_miles": 10.0,
            "pace_min_per_mile": "6:45",
            "workout_type": "tempo",
        }

        response = client.post("/runs/simple", json=run_data)
        assert response.status_code == 201

        run_detail = db_session.get(RunDetail, response.json()["id"])
        assert run_detail.workout_type.value == "tempo"

    def test_create_run_simple_pace_conversion_8_min_mile(
        self, client: TestClient, db_session: Session
    ):
        """Test pace conversion: 8:00 min/mile → 298 sec/km."""
        run_data = {
            "date": "2026-01-14",
            "distance_miles": 1.0,
            "pace_min_per_mile": "8:00",
        }

        response = client.post("/runs/simple", json=run_data)
        assert response.status_code == 201

        run_detail = db_session.get(RunDetail, response.json()["id"])
        # 8:00 min/mile = 480 sec/mile / 1.609344 = 298.26 → 298 sec/km
        assert run_detail.avg_pace_sec_per_km == 298

    def test_create_run_simple_distance_conversion(
        self, client: TestClient, db_session: Session
    ):
        """Test distance conversion: 1 mile = 1609 meters."""
        run_data = {
            "date": "2026-01-14",
            "distance_miles": 1.0,
            "pace_min_per_mile": "10:00",
        }

        response = client.post("/runs/simple", json=run_data)
        assert response.status_code == 201

        run_detail = db_session.get(RunDetail, response.json()["id"])
        # 1 mile * 1609.344 = 1609.344 → 1609 meters
        assert run_detail.distance_meters == 1609

    def test_create_run_simple_invalid_date_format(self, client: TestClient):
        """Test that invalid date format returns error."""
        run_data = {
            "date": "2026/01/14",  # Wrong format
            "distance_miles": 5.0,
            "pace_min_per_mile": "8:00",
        }

        response = client.post("/runs/simple", json=run_data)
        assert response.status_code == 422

    def test_create_run_simple_invalid_pace_format(self, client: TestClient):
        """Test that invalid pace format returns error."""
        run_data = {
            "date": "2026-01-14",
            "distance_miles": 5.0,
            "pace_min_per_mile": "8:60",  # Invalid: seconds must be 00-59
        }

        response = client.post("/runs/simple", json=run_data)
        assert response.status_code == 422

    def test_create_run_simple_zero_distance(self, client: TestClient):
        """Test that zero distance returns error."""
        run_data = {
            "date": "2026-01-14",
            "distance_miles": 0,
            "pace_min_per_mile": "8:00",
        }

        response = client.post("/runs/simple", json=run_data)
        assert response.status_code == 422


class TestHangoutsEndpoint:
    """Tests for the /hangouts endpoint."""

    def test_create_hangout_with_new_participants(
        self, client: TestClient, db_session: Session
    ):
        """Test creating a hangout creates activity, detail, and participants."""
        hangout_data = {
            "title": "Coffee with friends",
            "start_at": "2024-01-15T14:00:00+00:00",
            "end_at": "2024-01-15T16:00:00+00:00",
            "location_name": "Blue Bottle Coffee",
            "location_type": "cafe",
            "cost_estimate": 15.50,
            "mood": 4,
            "participants": [
                {"name": "Alice", "handle": "@alice"},
                {"name": "Bob"},
            ],
            "tags": ["coffee", "friends"],
        }

        response = client.post("/hangouts", json=hangout_data)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["participants_created"] == 2

        # Verify activity was created
        activity = db_session.get(Activity, data["id"])
        assert activity is not None
        assert activity.title == "Coffee with friends"
        assert activity.type.value == "hangout"

        # Verify hangout_detail was created
        hangout_detail = db_session.get(HangoutDetail, data["id"])
        assert hangout_detail is not None
        assert hangout_detail.location_name == "Blue Bottle Coffee"
        assert hangout_detail.mood == 4

        # Verify people were created
        people = db_session.execute(select(Person)).scalars().all()
        assert len(people) == 2
        names = {p.name for p in people}
        assert names == {"Alice", "Bob"}

        # Verify activity_participants were created
        participants = db_session.execute(
            select(ActivityParticipant).where(
                ActivityParticipant.activity_id == data["id"]
            )
        ).scalars().all()
        assert len(participants) == 2

    def test_create_hangout_reuses_existing_person(
        self, client: TestClient, db_session: Session
    ):
        """Test that existing people are reused, not duplicated."""
        # First hangout with Alice
        hangout1 = {
            "title": "First hangout",
            "start_at": "2024-01-15T14:00:00+00:00",
            "participants": [{"name": "Alice"}],
        }
        response1 = client.post("/hangouts", json=hangout1)
        assert response1.json()["participants_created"] == 1

        # Second hangout with Alice (should reuse)
        hangout2 = {
            "title": "Second hangout",
            "start_at": "2024-01-16T14:00:00+00:00",
            "participants": [{"name": "Alice"}],
        }
        response2 = client.post("/hangouts", json=hangout2)
        assert response2.json()["participants_created"] == 0

        # Should only have 1 person total
        people = db_session.execute(select(Person)).scalars().all()
        assert len(people) == 1

    def test_create_hangout_minimal(self, client: TestClient, db_session: Session):
        """Test creating a hangout with minimal data."""
        hangout_data = {
            "title": "Quick meetup",
            "start_at": "2024-01-15T14:00:00+00:00",
        }

        response = client.post("/hangouts", json=hangout_data)
        assert response.status_code == 201


class TestWorkSessionsEndpoint:
    """Tests for the /work-sessions endpoint."""

    def test_create_work_session_success(
        self, client: TestClient, db_session: Session
    ):
        """Test creating a work session."""
        work_data = {
            "title": "Implement user auth",
            "notes": "Added JWT tokens",
            "start_at": "2024-01-15T09:00:00+00:00",
            "end_at": "2024-01-15T12:00:00+00:00",
            "project": "goal-tracker",
            "area": "backend",
            "status": "in_progress",
            "artifact_link": "https://github.com/pr/123",
            "tags": ["auth", "backend"],
        }

        response = client.post("/work-sessions", json=work_data)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data

        activity = db_session.get(Activity, data["id"])
        assert activity is not None
        assert activity.type.value == "work"
        assert activity.duration_min == 180  # 3 hours


class TestWeeklyStatsEndpoint:
    """Tests for the /stats/weekly endpoint."""

    def test_weekly_stats_returns_expected_keys(self, client: TestClient):
        """Test that weekly stats returns all expected keys."""
        response = client.get(
            "/stats/weekly",
            params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "total_runs" in data
        assert "total_distance_meters" in data
        assert "total_run_duration_min" in data
        assert "total_hangouts" in data
        assert "total_work_sessions" in data
        assert "total_work_minutes" in data
        assert "weeks" in data
        assert isinstance(data["weeks"], list)

    def test_weekly_stats_with_data(self, client: TestClient, db_session: Session):
        """Test weekly stats aggregation with actual data."""
        # Create a run
        client.post(
            "/runs",
            json={
                "title": "Run 1",
                "start_at": "2024-01-15T07:00:00+00:00",
                "duration_min": 45,
                "distance_meters": 10000,
                "workout_type": "easy",
            },
        )

        # Create another run in same week
        client.post(
            "/runs",
            json={
                "title": "Run 2",
                "start_at": "2024-01-16T07:00:00+00:00",
                "duration_min": 30,
                "distance_meters": 5000,
                "workout_type": "recovery",
            },
        )

        # Create a hangout
        client.post(
            "/hangouts",
            json={
                "title": "Hangout",
                "start_at": "2024-01-15T19:00:00+00:00",
            },
        )

        # Create a work session
        client.post(
            "/work-sessions",
            json={
                "title": "Work",
                "start_at": "2024-01-15T09:00:00+00:00",
                "duration_min": 120,
                "project": "test",
            },
        )

        response = client.get(
            "/stats/weekly",
            params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["total_runs"] == 2
        assert data["total_distance_meters"] == 15000
        assert data["total_run_duration_min"] == 75
        assert data["total_hangouts"] == 1
        assert data["total_work_sessions"] == 1
        assert data["total_work_minutes"] == 120

        # Should have one week in breakdown
        assert len(data["weeks"]) == 1
        week = data["weeks"][0]
        assert week["runs_count"] == 2
        assert week["distance_meters"] == 15000
        assert week["hangouts_count"] == 1
        assert week["work_sessions_count"] == 1

    def test_weekly_stats_date_validation(self, client: TestClient):
        """Test that start_date must be before end_date."""
        response = client.get(
            "/stats/weekly",
            params={"start_date": "2024-01-31", "end_date": "2024-01-01"},
        )
        assert response.status_code == 400
