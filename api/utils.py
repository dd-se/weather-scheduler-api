from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones


def convert_utc_iso_to_target_timezone(utc_iso_str: str, target_timezone_str: str) -> datetime | None:
    """
    Converts an ISO-formatted UTC string to a datetime object in the specified target timezone.

    Args:
        utc_isoformat_str (str): The ISO-formatted UTC string to convert (e.g., '2023-10-05T14:30:00Z').
        target_timezone (str): The target timezone name (e.g., 'America/New_York').

    Returns:
        datetime | None: A timezone-aware datetime object in the target timezone if the input is valid and the timezone is recognized.
                         Returns None if the input string is malformed or not in ISO UTC format.
    """
    if target_timezone_str not in available_timezones():
        return

    try:
        if utc_iso_str.endswith("Z"):
            utc_iso_str = utc_iso_str.replace("Z", "+00:00")

        utc_dt = datetime.fromisoformat(utc_iso_str)
    except ValueError:
        return

    if utc_dt.tzinfo is not timezone.utc:
        return

    if target_timezone_str.upper() in ("UTC", "GMT"):
        return utc_dt

    target_timezone = ZoneInfo(target_timezone_str)
    return utc_dt.astimezone(target_timezone)


def celsius_to_fahrenheit(celsius: float) -> float:
    return round((celsius * 1.8) + 32, 2)
