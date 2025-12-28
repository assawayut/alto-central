"""Plant Performance Analytics API endpoints.

Provides aggregated analytics for water-side chiller plant performance.
"""

from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Path, Query

from app.db.connections import get_timescale
from app.core import (
    get_site_timezone,
    get_date_range,
    to_local_timestamp,
    parse_time_filter,
    filter_by_time_of_day,
    filter_by_day_type,
    get_table_for_resolution,
)

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
    - chs, cds, outdoor_wbt, outdoor_dbt

    Resolution determines which table to query:
    - 1m: aggregated_data
    - 15m: aggregated_data_15min
    - 1h: aggregated_data_1hour
    """
    # Get site timezone
    site_tz = get_site_timezone(site_id)

    # Calculate default date range (3 months ago to today)
    today = datetime.now(site_tz).date()
    if end_date is None:
        end_date = today
    if start_date is None:
        start_date = end_date - timedelta(days=90)

    # Parse time filters
    filter_start_time = parse_time_filter(start_time, time(0, 0))
    filter_end_time = parse_time_filter(end_time, time(23, 59))

    # Convert dates to UTC for database query
    start_utc, end_utc = get_date_range(start_date, end_date, site_tz)

    # Get table name based on resolution
    table_name = get_table_for_resolution(resolution)

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

    # Query plant-level data (power, cooling_rate)
    plant_query = f"""
        SELECT timestamp, datapoint, value
        FROM {table_name}
        WHERE site_id = $1
          AND device_id = 'plant'
          AND datapoint IN ('power', 'cooling_rate')
          AND timestamp >= $2
          AND timestamp < $3
        ORDER BY timestamp
    """

    # Query chilled water supply temperature
    chs_query = f"""
        SELECT timestamp, value
        FROM {table_name}
        WHERE site_id = $1
          AND device_id = 'chilled_water_loop'
          AND datapoint = 'supply_water_temperature'
          AND timestamp >= $2
          AND timestamp < $3
        ORDER BY timestamp
    """

    # Query condenser water supply temperature
    cds_query = f"""
        SELECT timestamp, value
        FROM {table_name}
        WHERE site_id = $1
          AND device_id = 'condenser_water_loop'
          AND datapoint = 'supply_water_temperature'
          AND timestamp >= $2
          AND timestamp < $3
        ORDER BY timestamp
    """

    # Query outdoor weather data
    weather_query = f"""
        SELECT timestamp, datapoint, value
        FROM {table_name}
        WHERE site_id = $1
          AND device_id = 'outdoor_weather_station'
          AND datapoint IN ('wetbulb_temperature', 'drybulb_temperature')
          AND timestamp >= $2
          AND timestamp < $3
        ORDER BY timestamp
    """

    # Query chiller status data to determine running chillers
    chiller_query = f"""
        SELECT timestamp, device_id, value
        FROM {table_name}
        WHERE site_id = $1
          AND device_id LIKE 'chiller_%%'
          AND datapoint = 'status_read'
          AND timestamp >= $2
          AND timestamp < $3
        ORDER BY timestamp, device_id
    """

    try:
        plant_rows = await timescale.fetch(plant_query, site_id, start_utc, end_utc)
        chs_rows = await timescale.fetch(chs_query, site_id, start_utc, end_utc)
        cds_rows = await timescale.fetch(cds_query, site_id, start_utc, end_utc)
        weather_rows = await timescale.fetch(weather_query, site_id, start_utc, end_utc)
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

    # Index CHS data by timestamp
    chs_data: Dict[datetime, float] = {}
    for row in chs_rows:
        chs_data[row["timestamp"]] = row["value"]

    # Index CDS data by timestamp
    cds_data: Dict[datetime, float] = {}
    for row in cds_rows:
        cds_data[row["timestamp"]] = row["value"]

    # Pivot weather data by timestamp
    weather_data: Dict[datetime, Dict[str, float]] = {}
    for row in weather_rows:
        ts = row["timestamp"]
        dp = row["datapoint"]
        val = row["value"]
        if ts not in weather_data:
            weather_data[ts] = {}
        weather_data[ts][dp] = val

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
        # Convert to site timezone for filtering and output
        ts_local = to_local_timestamp(ts, site_tz)

        # Apply time-of-day filter
        if not filter_by_time_of_day(ts_local, filter_start_time, filter_end_time):
            continue

        # Apply day type filter
        if not filter_by_day_type(ts_local, day_type):
            continue

        # Get plant values
        vals = plant_data[ts]
        power = vals.get("power")
        cooling_load = vals.get("cooling_rate")  # cooling_rate = cooling load in RT

        # Skip data points where cooling_load < 10 RT (avoid noise at very low loads)
        if cooling_load is None or cooling_load < 10:
            continue

        # Calculate efficiency (kW/RT)
        efficiency = None
        if power is not None and cooling_load > 0:
            efficiency = power / cooling_load

        # Get running chillers
        chillers = chiller_status.get(ts, {})
        running_chillers = sorted([
            ch_id.replace("chiller_", "CH-")
            for ch_id, status in chillers.items()
            if status and status >= 1
        ])
        num_chillers = len(running_chillers)
        chiller_combination = "+".join(running_chillers) if running_chillers else None

        # Get temperature data
        chs = chs_data.get(ts)
        cds = cds_data.get(ts)
        weather = weather_data.get(ts, {})
        outdoor_wbt = weather.get("wetbulb_temperature")
        outdoor_dbt = weather.get("drybulb_temperature")

        data_points.append({
            "timestamp": ts_local.isoformat(),  # Return in site's local timezone
            "cooling_load": round(cooling_load, 2) if cooling_load is not None else None,
            "power": round(power, 2) if power is not None else None,
            "efficiency": round(efficiency, 4) if efficiency is not None else None,
            "num_chillers": num_chillers,
            "chiller_combination": chiller_combination,
            "chs": round(chs, 2) if chs is not None else None,
            "cds": round(cds, 2) if cds is not None else None,
            "outdoor_wbt": round(outdoor_wbt, 2) if outdoor_wbt is not None else None,
            "outdoor_dbt": round(outdoor_dbt, 2) if outdoor_dbt is not None else None,
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
