"""Tests for unit conversion functions."""

import pytest

from app import conversions


class TestMilesToMeters:
    """Tests for miles_to_meters conversion."""

    def test_exact_conversion(self):
        """Test that 1 mile = 1609.344 meters."""
        assert conversions.miles_to_meters(1.0) == 1609

    def test_fractional_miles(self):
        """Test conversion with fractional miles."""
        # 5.5 miles = 8851.392 meters
        assert conversions.miles_to_meters(5.5) == 8851

    def test_large_distance(self):
        """Test conversion with larger distances."""
        # 26.2 miles (marathon) = 42164.813 meters
        assert conversions.miles_to_meters(26.2) == 42165


class TestMetersToMiles:
    """Tests for meters_to_miles conversion."""

    def test_exact_conversion(self):
        """Test that 1609.344 meters = 1 mile."""
        assert conversions.meters_to_miles(1609) == 1.0

    def test_round_trip(self):
        """Test that converting back and forth preserves value."""
        miles = 5.5
        meters = conversions.miles_to_meters(miles)
        back_to_miles = conversions.meters_to_miles(meters)
        assert abs(back_to_miles - miles) < 0.01  # Within 0.01 miles


class TestPaceConversions:
    """Tests for pace conversion between min/mile and sec/km."""

    def test_valid_pace_format(self):
        """Test converting valid mm:ss pace."""
        # 8:30/mile = 510 seconds/mile
        # 510 / 1.609344 ≈ 317 seconds/km
        result = conversions.pace_min_per_mile_to_sec_per_km("8:30")
        assert result == 317

    def test_single_digit_minutes(self):
        """Test pace with single digit minutes."""
        # 7:00/mile = 420 seconds/mile
        # 420 / 1.609344 ≈ 261 seconds/km
        result = conversions.pace_min_per_mile_to_sec_per_km("7:00")
        assert result == 261

    def test_fast_pace(self):
        """Test a fast pace conversion."""
        # 5:30/mile = 330 seconds/mile
        # 330 / 1.609344 ≈ 205 seconds/km
        result = conversions.pace_min_per_mile_to_sec_per_km("5:30")
        assert result == 205

    def test_slow_pace(self):
        """Test a slower pace conversion."""
        # 10:45/mile = 645 seconds/mile
        # 645 / 1.609344 ≈ 401 seconds/km
        result = conversions.pace_min_per_mile_to_sec_per_km("10:45")
        assert result == 401

    def test_invalid_format_raises_error(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Pace must be in mm:ss format"):
            conversions.pace_min_per_mile_to_sec_per_km("8-30")

    def test_invalid_seconds_raises_error(self):
        """Test that seconds > 59 raises ValueError."""
        with pytest.raises(ValueError, match="Pace must be in mm:ss format"):
            conversions.pace_min_per_mile_to_sec_per_km("8:60")

    def test_missing_colon_raises_error(self):
        """Test that missing colon raises ValueError."""
        with pytest.raises(ValueError, match="Pace must be in mm:ss format"):
            conversions.pace_min_per_mile_to_sec_per_km("830")


class TestSecPerKmToPaceStr:
    """Tests for converting sec/km back to display format."""

    def test_conversion_to_display(self):
        """Test converting sec/km to min/mile string."""
        # 317 sec/km ≈ 510 sec/mile ≈ 8:30/mile
        result = conversions.sec_per_km_to_pace_str(317)
        assert result == "8:30"

    def test_round_trip(self):
        """Test that converting pace string -> sec/km -> string preserves format."""
        original = "7:45"
        sec_per_km = conversions.pace_min_per_mile_to_sec_per_km(original)
        back_to_str = conversions.sec_per_km_to_pace_str(sec_per_km)
        # Allow small rounding differences
        original_parts = original.split(":")
        back_parts = back_to_str.split(":")
        assert abs(int(original_parts[0]) - int(back_parts[0])) <= 1
        assert abs(int(original_parts[1]) - int(back_parts[1])) <= 5


class TestEndToEndRunConversion:
    """Integration tests for full run data conversion."""

    def test_complete_run_conversion(self):
        """Test converting a complete run from UI units to DB units."""
        # User inputs
        distance_miles = 6.2  # 10K
        pace_str = "7:15"

        # Convert to DB units
        distance_meters = conversions.miles_to_meters(distance_miles)
        pace_sec_per_km = conversions.pace_min_per_mile_to_sec_per_km(pace_str)

        # Verify conversions
        assert distance_meters == 9978  # 6.2 miles = 9978 meters
        assert pace_sec_per_km == 270  # 7:15/mile ≈ 270 sec/km

        # Verify round-trip back to display
        display_miles = conversions.meters_to_miles(distance_meters)
        display_pace = conversions.sec_per_km_to_pace_str(pace_sec_per_km)

        assert abs(display_miles - distance_miles) < 0.01
        # Pace should be close (allowing for rounding)
        assert display_pace in ["7:14", "7:15", "7:16"]
