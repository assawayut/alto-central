"""Core utilities and shared functionality."""

from app.core.exceptions import (
    AltoException,
    NotFoundException,
    DatabaseException,
    ValidationException,
)
from app.core.logging import setup_logging, get_logger
from app.core.time_utils import (
    get_site_timezone,
    get_today_range,
    get_yesterday_range,
    get_date_range,
    to_local_timestamp,
    parse_time_filter,
    filter_by_time_of_day,
    filter_by_day_type,
    get_table_for_resolution,
    RESOLUTION_TABLES,
)

__all__ = [
    # Exceptions
    "AltoException",
    "NotFoundException",
    "DatabaseException",
    "ValidationException",
    # Logging
    "setup_logging",
    "get_logger",
    # Time utilities
    "get_site_timezone",
    "get_today_range",
    "get_yesterday_range",
    "get_date_range",
    "to_local_timestamp",
    "parse_time_filter",
    "filter_by_time_of_day",
    "filter_by_day_type",
    "get_table_for_resolution",
    "RESOLUTION_TABLES",
]
