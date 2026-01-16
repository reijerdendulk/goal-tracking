"""Unit conversion utilities for runs data entry."""

import re


def miles_to_meters(miles: float) -> int:
    """
    Convert miles to meters.

    Args:
        miles: Distance in miles

    Returns:
        Distance in meters (rounded to nearest integer)
    """
    return round(miles * 1609.344)


def pace_min_per_mile_to_sec_per_km(pace_str: str) -> int:
    """
    Convert pace from min/mile (mm:ss format) to sec/km.

    Args:
        pace_str: Pace in "mm:ss" format (e.g., "8:30")

    Returns:
        Pace in seconds per kilometer

    Raises:
        ValueError: If pace format is invalid
    """
    match = re.match(r'^(\d+):([0-5]\d)$', pace_str.strip())
    if not match:
        raise ValueError(
            "Pace must be in mm:ss format (e.g., 8:30) with seconds 00-59"
        )

    minutes = int(match.group(1))
    seconds = int(match.group(2))

    # Convert to total seconds per mile
    sec_per_mile = minutes * 60 + seconds

    # Convert miles to km: 1 mile = 1.609344 km
    # sec/km = sec/mile / 1.609344
    sec_per_km = sec_per_mile / 1.609344

    return round(sec_per_km)


def sec_per_km_to_pace_str(sec_per_km: int) -> str:
    """
    Convert pace from sec/km to min/mile display format.

    Args:
        sec_per_km: Pace in seconds per kilometer

    Returns:
        Pace in "mm:ss" format
    """
    # Convert km to miles: sec/mile = sec/km * 1.609344
    sec_per_mile = sec_per_km * 1.609344
    minutes = int(sec_per_mile // 60)
    seconds = int(sec_per_mile % 60)
    return f"{minutes}:{seconds:02d}"


def meters_to_miles(meters: int) -> float:
    """
    Convert meters to miles.

    Args:
        meters: Distance in meters

    Returns:
        Distance in miles (rounded to 2 decimal places)
    """
    return round(meters / 1609.344, 2)
