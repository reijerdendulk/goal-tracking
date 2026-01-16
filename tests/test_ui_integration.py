"""Integration tests for UI data entry with unit conversions."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import conversions
from app.models import Activity, RunDetail


class TestRunUIIntegration:
    """Test run creation via JSON API with unit conversions."""

    def test_create_run_with_converted_units(
        self, client: TestClient, db_session: Session
    ):
        """
        Verify that inserting a run with miles/min-per-mile via JSON API
        results in correct meters/sec-per-km in the database.
        """
        # User inputs (in miles and min/mile)
        distance_miles = 5.5
        pace_str = "8:30"  # 8 minutes 30 seconds per mile

        # Convert to database units
        distance_meters = conversions.miles_to_meters(distance_miles)
        avg_pace_sec_per_km = conversions.pace_min_per_mile_to_sec_per_km(pace_str)

        # Create run via JSON API (canonical interface)
        run_data = {
            "title": f"Run - {distance_miles} mi",
            "start_at": "2024-01-15T12:00:00+00:00",
            "distance_meters": distance_meters,
            "avg_pace_sec_per_km": avg_pace_sec_per_km,
            "workout_type": "easy",
        }

        response = client.post("/runs", json=run_data)
        assert response.status_code == 201

        data = response.json()
        activity_id = data["id"]

        # Verify activity row
        activity = db_session.get(Activity, activity_id)
        assert activity is not None
        assert activity.type.value == "run"
        assert activity.title == "Run - 5.5 mi"

        # Verify run_detail row has correct unit conversions
        run_detail = db_session.get(RunDetail, activity_id)
        assert run_detail is not None

        # Verify distance conversion: 5.5 miles = 8851 meters
        assert run_detail.distance_meters == 8851

        # Verify pace conversion: 8:30/mile ≈ 317 sec/km
        assert run_detail.avg_pace_sec_per_km == 317

        # Verify round-trip conversion back to display units
        display_miles = conversions.meters_to_miles(run_detail.distance_meters)
        display_pace = conversions.sec_per_km_to_pace_str(
            run_detail.avg_pace_sec_per_km
        )

        assert abs(display_miles - distance_miles) < 0.01
        assert display_pace in ["8:29", "8:30", "8:31"]  # Allow rounding

    def test_create_multiple_runs_with_different_paces(
        self, client: TestClient, db_session: Session
    ):
        """Test creating multiple runs with different pace conversions."""
        test_cases = [
            (3.1, "7:00"),  # 5K at 7:00/mile
            (6.2, "7:30"),  # 10K at 7:30/mile
            (13.1, "8:15"),  # Half marathon at 8:15/mile
        ]

        for distance_miles, pace_str in test_cases:
            distance_meters = conversions.miles_to_meters(distance_miles)
            pace_sec_per_km = conversions.pace_min_per_mile_to_sec_per_km(pace_str)

            run_data = {
                "title": f"{distance_miles} mile run",
                "start_at": datetime.now(timezone.utc).isoformat(),
                "distance_meters": distance_meters,
                "avg_pace_sec_per_km": pace_sec_per_km,
                "workout_type": "easy",
            }

            response = client.post("/runs", json=run_data)
            assert response.status_code == 201

            # Verify DB has correct conversions
            run_detail = db_session.get(RunDetail, response.json()["id"])
            assert run_detail is not None
            assert run_detail.distance_meters == distance_meters
            assert run_detail.avg_pace_sec_per_km == pace_sec_per_km

    def test_pace_conversion_precision(self, client: TestClient, db_session: Session):
        """Test that pace conversions are precise and consistent."""
        # Test with a specific pace that should convert cleanly
        distance_miles = 10.0
        pace_str = "6:00"  # 6:00/mile = 360 sec/mile

        distance_meters = conversions.miles_to_meters(distance_miles)
        pace_sec_per_km = conversions.pace_min_per_mile_to_sec_per_km(pace_str)

        run_data = {
            "title": "10 mile tempo",
            "start_at": "2024-01-15T08:00:00+00:00",
            "distance_meters": distance_meters,
            "avg_pace_sec_per_km": pace_sec_per_km,
            "workout_type": "tempo",
        }

        response = client.post("/runs", json=run_data)
        assert response.status_code == 201

        run_detail = db_session.get(RunDetail, response.json()["id"])
        assert run_detail is not None

        # 10 miles = 16093 meters
        assert run_detail.distance_meters == 16093

        # 6:00/mile = 360 sec/mile
        # 360 / 1.609344 ≈ 224 sec/km
        assert run_detail.avg_pace_sec_per_km == 224


class TestConversionConstants:
    """Test that conversion constants are correct."""

    def test_miles_to_meters_constant(self):
        """Verify 1 mile = 1609.344 meters."""
        assert conversions.miles_to_meters(1.0) == 1609

    def test_marathon_distance(self):
        """Verify marathon distance conversion."""
        # 26.2 miles (marathon) should be ~42195 meters (official 42.195 km)
        marathon_miles = 26.2
        marathon_meters = conversions.miles_to_meters(marathon_miles)

        # Should be within 50 meters of official distance
        assert abs(marathon_meters - 42195) < 50
