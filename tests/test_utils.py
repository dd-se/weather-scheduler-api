from pytest import approx

from api.utils import celsius_to_fahrenheit, convert_utc_iso_to_target_timezone


def test_utc_isoformat_to_target_timezone():
    # Test valid UTC to America/New_York conversion
    utc_str = "2025-08-29T12:00:00+00:00"
    result = convert_utc_iso_to_target_timezone(utc_str, "America/New_York")
    assert result is not None
    assert result.tzname() == "EDT"  # During DST
    assert result.isoformat() == "2025-08-29T08:00:00-04:00"  # Verify converted time

    # Test invalid timezone
    result = convert_utc_iso_to_target_timezone(utc_str, "Invalid/Timezone")
    assert result is None

    # Test invalid UTC string format
    result = convert_utc_iso_to_target_timezone("invalid-date", "America/New_York")
    assert result is None

    # Test non-UTC input
    non_utc_str = "2025-08-29T12:00:00+01:00"
    result = convert_utc_iso_to_target_timezone(non_utc_str, "America/New_York")
    assert result is None

    # Test valid UTC to Europe/Stockholm during DST
    result = convert_utc_iso_to_target_timezone(utc_str, "Europe/Stockholm")
    assert result is not None
    assert result.tzname() == "CEST"  # During DST
    assert result.isoformat() == "2025-08-29T14:00:00+02:00"  # Verify converted time

    # Test valid UTC to Europe/Stockholm outside DST
    winter_utc_str = "2025-01-01T12:00:00+00:00"
    result = convert_utc_iso_to_target_timezone(winter_utc_str, "Europe/Stockholm")
    assert result is not None
    assert result.tzname() == "CET"  # No DST
    assert result.isoformat() == "2025-01-01T13:00:00+01:00"  # Verify converted time

    # Test UTC to UTC (should remain the same)
    result = convert_utc_iso_to_target_timezone(utc_str, "UTC")
    assert result is not None
    assert result.tzname() == "UTC"
    assert result.isoformat() == "2025-08-29T12:00:00+00:00"

    # Test with Z instead of +00:00
    utc_str_z = "2025-08-29T12:00:00Z"
    result = convert_utc_iso_to_target_timezone(utc_str_z, "Europe/Stockholm")
    assert result is not None
    assert result.tzname() == "CEST"
    assert result.isoformat() == "2025-08-29T14:00:00+02:00"

    # Test with microseconds
    utc_str_micro = "2025-08-29T12:00:00.123456+00:00"
    result = convert_utc_iso_to_target_timezone(utc_str_micro, "Europe/Stockholm")
    assert result is not None
    assert result.tzname() == "CEST"
    assert result.isoformat() == "2025-08-29T14:00:00.123456+02:00"


def test_celsius_to_fahrenheit():
    assert celsius_to_fahrenheit(0) == approx(32.0)
    assert celsius_to_fahrenheit(100) == approx(212.0)
    assert celsius_to_fahrenheit(-40) == approx(-40.0)
    assert celsius_to_fahrenheit(37.5) == approx(99.5)
    assert celsius_to_fahrenheit(-10.5) == approx(13.1)
    assert celsius_to_fahrenheit(1000) == approx(1832.0)
    assert celsius_to_fahrenheit(-273.15) == approx(-459.67)
    assert celsius_to_fahrenheit(0.0) == approx(32.0)
    assert celsius_to_fahrenheit(-5) == approx(23.0)
    assert celsius_to_fahrenheit(20) == approx(68.0)
