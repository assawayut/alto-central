"""Timeseries data API endpoints.

These endpoints provide historical timeseries data from TimescaleDB (READ-ONLY).
Each site can have its own TimescaleDB instance configured in sites.yaml.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Path, Query

from app.db.connections import get_timescale
from app.config import get_site_by_id
from app.models.schemas.timeseries import (
    TimeseriesQuery,
    TimeseriesDataPoint,
    TimeseriesResult,
    TimeseriesResponse,
)

router = APIRouter()


@router.post(
    "/query",
    response_model=TimeseriesResponse,
    summary="Query timeseries data",
    description="Query historical timeseries data with optional resampling.",
)
async def query_timeseries(
    site_id: str = Path(..., description="Site identifier"),
    query: TimeseriesQuery = ...,
) -> TimeseriesResponse:
    """Query timeseries data for specified datapoints.

    Supports resampling intervals: 1m, 5m, 15m, 30m, 1h, 6h, 1d
    """
    # Get site-specific TimescaleDB connection
    timescale = await get_timescale(site_id)

    # Convert resample string to PostgreSQL interval
    resample_map = {
        "1m": "1 minute",
        "5m": "5 minutes",
        "15m": "15 minutes",
        "30m": "30 minutes",
        "1h": "1 hour",
        "6h": "6 hours",
        "1d": "1 day",
    }
    resample_interval = resample_map.get(query.resampling) if query.resampling else None

    # Query TimescaleDB
    rows = await timescale.query_timeseries(
        device_id=query.device_id,
        datapoints=query.datapoints,
        start_time=query.start_timestamp,
        end_time=query.end_timestamp,
        resample=resample_interval,
    )

    # Group results by datapoint
    datapoint_values: Dict[str, List[TimeseriesDataPoint]] = {}
    for row in rows:
        dp = row["datapoint"]
        if dp not in datapoint_values:
            datapoint_values[dp] = []
        datapoint_values[dp].append(
            TimeseriesDataPoint(
                timestamp=row["timestamp"],
                value=row["value"],
            )
        )

    # Build response
    results = [
        TimeseriesResult(
            device_id=query.device_id,
            datapoint=dp,
            values=values,
        )
        for dp, values in datapoint_values.items()
    ]

    return TimeseriesResponse(
        site_id=site_id,
        query=query,
        data=results,
    )


@router.get(
    "/aggregated",
    summary="Get pre-aggregated timeseries data",
    description="Get hourly or daily aggregated data for common use cases.",
)
async def get_aggregated_data(
    site_id: str = Path(..., description="Site identifier"),
    device_id: str = Query("plant", description="Device identifier"),
    datapoint: str = Query("power", description="Datapoint name"),
    period: str = Query("24h", description="Time period (24h, 7d, 30d, today, yesterday)"),
    aggregation: str = Query("hourly", description="Aggregation level (hourly, daily)"),
) -> Dict:
    """Get pre-aggregated timeseries data.

    This is optimized for common dashboard queries.

    Period options:
    - 24h, 7d, 30d: Rolling windows from current time (UTC)
    - today: From midnight to now in site's local timezone
    - yesterday: Full previous day in site's local timezone
    """
    # Get site-specific TimescaleDB connection
    timescale = await get_timescale(site_id)

    # Get site config for timezone
    site = get_site_by_id(site_id)
    site_tz = ZoneInfo(site.timezone) if site else ZoneInfo("UTC")

    # Calculate time range based on period
    # Note: Keep timezone info for asyncpg - it handles UTC conversion properly
    if period == "today":
        # Today: from midnight in site's timezone to now
        now_local = datetime.now(site_tz)
        start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        # Convert to UTC for database query (keep tzinfo for asyncpg)
        start_time = start_local.astimezone(timezone.utc)
        end_time = now_local.astimezone(timezone.utc)
    elif period == "yesterday":
        # Yesterday: full previous day in site's timezone
        now_local = datetime.now(site_tz)
        today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start_local = today_start_local - timedelta(days=1)
        # Convert to UTC for database query (keep tzinfo for asyncpg)
        start_time = yesterday_start_local.astimezone(timezone.utc)
        end_time = today_start_local.astimezone(timezone.utc)
    else:
        # Rolling window periods (24h, 7d, 30d)
        now = datetime.now(timezone.utc)
        period_map = {
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        delta = period_map.get(period, timedelta(hours=24))
        start_time = now - delta
        end_time = now

    # Determine resample interval
    resample = "1 hour" if aggregation == "hourly" else "1 day"

    # Query data
    rows = await timescale.query_timeseries(
        device_id=device_id,
        datapoints=[datapoint],
        start_time=start_time,
        end_time=end_time,
        resample=resample,
    )

    return {
        "site_id": site_id,
        "device_id": device_id,
        "datapoint": datapoint,
        "period": period,
        "aggregation": aggregation,
        "data": [
            {"timestamp": row["timestamp"].isoformat(), "value": row["value"]}
            for row in rows
        ],
    }


@router.get(
    "/latest-from-history",
    summary="Get latest values from timeseries",
    description="Fallback for getting latest values when Supabase is unavailable.",
)
async def get_latest_from_history(
    site_id: str = Path(..., description="Site identifier"),
) -> Dict:
    """Get latest values by querying TimescaleDB directly.

    This is a fallback when Supabase latest_data is not available.
    """
    # Get site-specific TimescaleDB connection
    timescale = await get_timescale(site_id)
    rows = await timescale.query_latest()

    # Transform to nested structure
    result: Dict[str, Dict] = {}
    for row in rows:
        device_id = row["device_id"]
        datapoint = row["datapoint"]
        if device_id not in result:
            result[device_id] = {}
        result[device_id][datapoint] = {
            "value": row["value"],
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        }

    return {
        "site_id": site_id,
        "source": "timescaledb",
        "devices": result,
    }
