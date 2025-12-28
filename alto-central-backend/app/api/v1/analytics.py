"""Plant Performance Analytics API endpoints.

Provides aggregated analytics for water-side chiller plant performance.
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Path, Query

from app.db.connections import get_timescale
from app.config import get_site_by_id

router = APIRouter()


@router.get(
    "/plant-performance",
    summary="Get plant performance analytics",
    description="Analyze chiller plant efficiency with filtering by date, time of day, and day type.",
)
async def get_plant_performance(
    site_id: str = Path(..., description="Site identifier"),
    start_date: Optional[date] = Query(
        None, description="Start date (YYYY-MM-DD). Default: 3 months ago"
    ),
    end_date: Optional[date] = Query(
        None, description="End date (YYYY-MM-DD). Default: today"
    ),
    resolution: str = Query(
        "1h", description="Data resolution", enum=["1m", "15m", "1h"]
    ),
    start_time: str = Query(
        "00:00", description="Filter start time of day (HH:MM)"
    ),
    end_time: str = Query(
        "23:59", description="Filter end time of day (HH:MM)"
    ),
    day_type: str = Query(
        "all", description="Filter by day type", enum=["all", "weekdays", "weekends"]
    ),
) -> Dict:
    """Get plant performance analytics for water-side chiller plants.

    Returns time series data with:
    - cooling_load (RT), power (kW), efficiency (kW/RT)
    - num_chillers, chiller_combination
    - chs_temp, cds_temp, outdoor_temp

    Resolution determines which table to query:
    - 1m: aggregated_data
    - 15m: aggregated_data_15min
    - 1h: aggregated_data_1hour
    """
    # Get site config for timezone
    site = get_site_by_id(site_id)
    site_tz = ZoneInfo(site.timezone) if site else ZoneInfo("UTC")

    # Calculate default date range (3 months ago to today)
    today = datetime.now(site_tz).date()
    if end_date is None:
        end_date = today
    if start_date is None:
        start_date = end_date - timedelta(days=90)

    # Parse time filters
    try:
        filter_start_time = datetime.strptime(start_time, "%H:%M").time()
        filter_end_time = datetime.strptime(end_time, "%H:%M").time()
    except ValueError:
        filter_start_time = time(0, 0)
        filter_end_time = time(23, 59)

    # Convert dates to timezone-aware datetimes for query
    start_dt = datetime.combine(start_date, time(0, 0), tzinfo=site_tz)
    end_dt = datetime.combine(end_date, time(23, 59, 59), tzinfo=site_tz)

    # Convert to UTC for database query
    start_utc = start_dt.astimezone(timezone.utc)
    end_utc = end_dt.astimezone(timezone.utc)

    # Determine table based on resolution
    table_map = {
        "1m": "aggregated_data",
        "15m": "aggregated_data_15min",
        "1h": "aggregated_data_1hour",
    }
    table_name = table_map.get(resolution, "aggregated_data_1hour")

    # Get TimescaleDB connection
    timescale = await get_timescale(site_id)

    if not timescale.is_connected:
        return {
            "site_id": site_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "resolution": resolution,
            "filters": {
                "start_time": start_time,
                "end_time": end_time,
                "day_type": day_type,
            },
            "data": [],
            "message": "TimescaleDB not connected",
        }

    # Query plant-level data
    # Note: datapoint names in database:
    # - cooling_rate = cooling load in RT
    # - power = total plant power in kW
    # - efficiency = pre-calculated kW/RT
    plant_query = f"""
        SELECT timestamp, datapoint, value
        FROM {table_name}
        WHERE site_id = $1
          AND device_id = 'plant'
          AND datapoint IN ('power', 'cooling_rate', 'efficiency')
          AND timestamp >= $2
          AND timestamp < $3
        ORDER BY timestamp
    """

    # Query chiller status data to determine running chillers
    chiller_query = f"""
        SELECT timestamp, device_id, value
        FROM {table_name}
        WHERE site_id = $1
          AND device_id LIKE 'ch%%'
          AND datapoint = 'status_read'
          AND timestamp >= $2
          AND timestamp < $3
        ORDER BY timestamp, device_id
    """

    try:
        plant_rows = await timescale.fetch(plant_query, site_id, start_utc, end_utc)
        chiller_rows = await timescale.fetch(chiller_query, site_id, start_utc, end_utc)
    except Exception as e:
        return {
            "site_id": site_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "resolution": resolution,
            "error": str(e),
            "data": [],
        }

    # Pivot plant data by timestamp
    plant_data: Dict[datetime, Dict[str, float]] = {}
    for row in plant_rows:
        ts = row["timestamp"]
        dp = row["datapoint"]
        val = row["value"]
        if ts not in plant_data:
            plant_data[ts] = {}
        plant_data[ts][dp] = val

    # Group chiller status by timestamp
    chiller_status: Dict[datetime, Dict[str, float]] = {}
    for row in chiller_rows:
        ts = row["timestamp"]
        device_id = row["device_id"]
        val = row["value"]
        if ts not in chiller_status:
            chiller_status[ts] = {}
        chiller_status[ts][device_id] = val

    # Build response data points
    data_points = []
    for ts in sorted(plant_data.keys()):
        # Convert to site timezone for filtering
        ts_local = ts.astimezone(site_tz) if ts.tzinfo else ts.replace(tzinfo=timezone.utc).astimezone(site_tz)

        # Apply time-of-day filter
        ts_time = ts_local.time()
        if not (filter_start_time <= ts_time <= filter_end_time):
            continue

        # Apply day type filter
        weekday = ts_local.weekday()  # 0=Monday, 6=Sunday
        if day_type == "weekdays" and weekday >= 5:
            continue
        if day_type == "weekends" and weekday < 5:
            continue

        # Get plant values
        vals = plant_data[ts]
        power = vals.get("power")
        cooling_load = vals.get("cooling_rate")  # cooling_rate = cooling load in RT
        efficiency = vals.get("efficiency")  # Pre-calculated kW/RT from database

        # Get running chillers
        chillers = chiller_status.get(ts, {})
        running_chillers = sorted([
            ch_id.upper().replace("_", "-")
            for ch_id, status in chillers.items()
            if status and status >= 1
        ])
        num_chillers = len(running_chillers)
        chiller_combination = "+".join(running_chillers) if running_chillers else None

        data_points.append({
            "timestamp": ts.isoformat(),
            "cooling_load": round(cooling_load, 2) if cooling_load is not None else None,
            "power": round(power, 2) if power is not None else None,
            "efficiency": round(efficiency, 4) if efficiency is not None else None,
            "num_chillers": num_chillers,
            "chiller_combination": chiller_combination,
        })

    return {
        "site_id": site_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "resolution": resolution,
        "filters": {
            "start_time": start_time,
            "end_time": end_time,
            "day_type": day_type,
        },
        "count": len(data_points),
        "data": data_points,
    }
