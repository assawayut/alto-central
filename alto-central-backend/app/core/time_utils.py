"""Time and timezone utilities for API endpoints.

Reusable functions for:
- Site timezone handling
- Date range calculations (today, yesterday, custom)
- Resolution-based table selection
- Time-of-day and day-type filtering
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from app.config import get_site_by_id


def get_site_timezone(site_id: str) -> ZoneInfo:
    """Get the timezone for a site.

    Returns UTC if site not found or timezone not configured.
    """
    site = get_site_by_id(site_id)
    return ZoneInfo(site.timezone) if site else ZoneInfo("UTC")


def get_today_range(site_tz: ZoneInfo) -> Tuple[datetime, datetime]:
    """Get today's date range in UTC (from midnight in site timezone to now).

    Returns:
        Tuple of (start_utc, end_utc) as timezone-aware datetimes
    """
    now_local = datetime.now(site_tz)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        start_local.astimezone(timezone.utc),
        now_local.astimezone(timezone.utc),
    )


def get_yesterday_range(site_tz: ZoneInfo) -> Tuple[datetime, datetime]:
    """Get yesterday's full date range in UTC.

    Returns:
        Tuple of (start_utc, end_utc) as timezone-aware datetimes
    """
    now_local = datetime.now(site_tz)
    today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start_local = today_start_local - timedelta(days=1)
    return (
        yesterday_start_local.astimezone(timezone.utc),
        today_start_local.astimezone(timezone.utc),
    )


def get_date_range(
    start_date: date,
    end_date: date,
    site_tz: ZoneInfo,
) -> Tuple[datetime, datetime]:
    """Convert date range to UTC datetimes.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        site_tz: Site timezone

    Returns:
        Tuple of (start_utc, end_utc) as timezone-aware datetimes
    """
    start_dt = datetime.combine(start_date, time(0, 0), tzinfo=site_tz)
    end_dt = datetime.combine(end_date, time(23, 59, 59), tzinfo=site_tz)
    return (
        start_dt.astimezone(timezone.utc),
        end_dt.astimezone(timezone.utc),
    )


def to_local_timestamp(ts: datetime, site_tz: ZoneInfo) -> datetime:
    """Convert a timestamp to site's local timezone.

    Handles both timezone-aware and naive (assumed UTC) datetimes.
    """
    if ts.tzinfo:
        return ts.astimezone(site_tz)
    return ts.replace(tzinfo=timezone.utc).astimezone(site_tz)


def parse_time_filter(time_str: str, default: time) -> time:
    """Parse HH:MM string to time object.

    Returns default if parsing fails.
    """
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return default


def filter_by_time_of_day(
    ts_local: datetime,
    start_time: time,
    end_time: time,
) -> bool:
    """Check if timestamp falls within time-of-day range.

    Returns True if timestamp's time is between start_time and end_time.
    """
    ts_time = ts_local.time()
    return start_time <= ts_time <= end_time


def filter_by_day_type(ts_local: datetime, day_type: str) -> bool:
    """Check if timestamp matches day type filter.

    Args:
        ts_local: Timestamp in local timezone
        day_type: "all", "weekdays", or "weekends"

    Returns True if timestamp matches the day type.
    """
    if day_type == "all":
        return True
    weekday = ts_local.weekday()  # 0=Monday, 6=Sunday
    if day_type == "weekdays":
        return weekday < 5
    if day_type == "weekends":
        return weekday >= 5
    return True


# Resolution to table mapping
RESOLUTION_TABLES = {
    "1m": "aggregated_data",
    "15m": "aggregated_data_15min",
    "1h": "aggregated_data_1hour",
}


def get_table_for_resolution(resolution: str) -> str:
    """Get the appropriate table name for a resolution.

    Args:
        resolution: "1m", "15m", or "1h"

    Returns:
        Table name (defaults to 1-hour table if unknown resolution)
    """
    return RESOLUTION_TABLES.get(resolution, "aggregated_data_1hour")
