"""Data fetching tools for AI-powered analytics.

These tools allow Claude to query TimescaleDB and Supabase
for historical and real-time HVAC data.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import statistics

from app.db.connections import get_timescale, get_supabase
from app.config import get_site_by_id

logger = logging.getLogger(__name__)


# HVAC-specific valid ranges for common datapoints
# Values outside these ranges are considered outliers/sensor errors
HVAC_VALUE_BOUNDS: Dict[str, Tuple[float, float]] = {
    # Efficiency: realistic range for water-cooled chillers
    "efficiency": (0.3, 2.0),  # kW/RT
    # Power: no negative values, reasonable max
    "power": (0, 10000),  # kW
    # Cooling/heating rates
    "cooling_rate": (0, 10000),  # RT
    "heat_reject": (0, 15000),  # RT
    # Temperatures: reasonable HVAC ranges
    "supply_water_temperature": (30, 100),  # °F
    "return_water_temperature": (30, 100),  # °F
    "evap_leaving_water_temperature": (30, 70),  # °F - chilled water leaving evaporator
    "evap_entering_water_temperature": (35, 80),  # °F - chilled water entering evaporator
    "cond_leaving_water_temperature": (70, 120),  # °F - condenser water leaving
    "cond_entering_water_temperature": (60, 110),  # °F - condenser water entering
    "drybulb_temperature": (0, 130),  # °F - outdoor temp
    "wetbulb_temperature": (0, 100),  # °F - outdoor wet bulb
    # Flow rates
    "flow_rate": (0, 50000),  # GPM
    # Percentages
    "percentage_rla": (0, 150),  # % - can exceed 100 briefly
    "humidity": (0, 100),  # %
}


def _filter_outliers_iqr(
    values: List[float],
    multiplier: float = 1.5,
) -> Tuple[float, float]:
    """Calculate outlier bounds using IQR method.

    Args:
        values: List of numeric values
        multiplier: IQR multiplier (1.5 = standard, 3.0 = extreme only)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if len(values) < 4:
        return (min(values), max(values))

    sorted_values = sorted(values)
    n = len(sorted_values)
    q1_idx = n // 4
    q3_idx = (3 * n) // 4

    q1 = sorted_values[q1_idx]
    q3 = sorted_values[q3_idx]
    iqr = q3 - q1

    lower_bound = q1 - (multiplier * iqr)
    upper_bound = q3 + (multiplier * iqr)

    return (lower_bound, upper_bound)


def _apply_outlier_filter(
    data: List[Dict[str, Any]],
    datapoints: List[str],
    method: str = "iqr",
    iqr_multiplier: float = 1.5,
    use_hvac_bounds: bool = True,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Apply outlier filtering to timeseries data.

    Args:
        data: List of records with timestamp and datapoint values
        datapoints: List of datapoint names to filter
        method: Filtering method - "iqr", "hvac_bounds", or "both"
        iqr_multiplier: IQR multiplier for statistical filtering
        use_hvac_bounds: Whether to apply HVAC-specific bounds

    Returns:
        Tuple of (filtered_data, filter_stats)
    """
    if not data:
        return data, {}

    filter_stats = {
        "original_count": len(data),
        "filtered_count": 0,
        "removed_count": 0,
        "bounds": {},
    }

    # Calculate bounds for each datapoint
    bounds: Dict[str, Tuple[float, float]] = {}

    for dp in datapoints:
        # Collect all values for this datapoint
        values = [
            record[dp] for record in data
            if dp in record and record[dp] is not None
        ]

        if not values:
            continue

        # Start with infinite bounds
        lower, upper = float('-inf'), float('inf')

        # Apply IQR-based bounds
        if method in ("iqr", "both"):
            iqr_lower, iqr_upper = _filter_outliers_iqr(values, iqr_multiplier)
            lower = max(lower, iqr_lower)
            upper = min(upper, iqr_upper)

        # Apply HVAC-specific bounds
        if use_hvac_bounds and dp in HVAC_VALUE_BOUNDS:
            hvac_lower, hvac_upper = HVAC_VALUE_BOUNDS[dp]
            lower = max(lower, hvac_lower)
            upper = min(upper, hvac_upper)

        bounds[dp] = (lower, upper)
        filter_stats["bounds"][dp] = {"lower": round(lower, 2), "upper": round(upper, 2)}

    # Filter data
    filtered_data = []
    for record in data:
        keep = True
        for dp in datapoints:
            if dp not in record or record[dp] is None:
                continue
            if dp in bounds:
                lower, upper = bounds[dp]
                if not (lower <= record[dp] <= upper):
                    keep = False
                    break
        if keep:
            filtered_data.append(record)

    filter_stats["filtered_count"] = len(filtered_data)
    filter_stats["removed_count"] = len(data) - len(filtered_data)

    return filtered_data, filter_stats


# Tool definitions for Claude API
QUERY_TIMESERIES_TOOL = {
    "name": "query_timeseries",
    "description": """Query historical timeseries data from the database.
Use this to fetch historical sensor data like power, temperature, flow rates.
Returns timestamped data that can be used for trend analysis and charts.

IMPORTANT: Use the exact device IDs from the user's prompt.
Example: "compare chiller_1 and chiller_2" -> query chiller_1 and chiller_2 separately.

Device ID patterns:
- plant: aggregate plant data
- chiller_{N}: individual chillers (chiller_1, chiller_2, chiller_3, ...)
- cooling_tower_{N}: cooling towers (cooling_tower_1, cooling_tower_2, ...)
- chilled_water_loop, condenser_water_loop: water loops
- outdoor_weather_station: weather data
- pchp_{N}, schp_{N}, cdwp_{N}: pumps

Common datapoints:
- chiller: power, cooling_rate, percentage_rla, evap_leaving_water_temperature, cond_entering_water_temperature
- plant: power, cooling_rate, efficiency, heat_reject
- loops: supply_water_temperature, return_water_temperature, flow_rate
- weather: drybulb_temperature, wetbulb_temperature, humidity""",
    "input_schema": {
        "type": "object",
        "properties": {
            "device_id": {
                "type": "string",
                "description": "Device ID (e.g., 'plant', 'chiller_1', 'chilled_water_loop')",
            },
            "datapoints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of datapoint names (e.g., ['power', 'cooling_rate'])",
            },
            "start_time": {
                "type": "string",
                "description": "Start time - either ISO 8601 timestamp or relative like '7d', '24h', '1h'",
            },
            "end_time": {
                "type": "string",
                "description": "End time - ISO 8601 timestamp or 'now'",
            },
            "resample": {
                "type": "string",
                "enum": ["1m", "5m", "15m", "1h", "1d"],
                "description": "Resampling interval for aggregation",
            },
            "filter_outliers": {
                "type": "boolean",
                "description": "Filter out outliers using IQR + HVAC bounds (default: true)",
                "default": True,
            },
            "min_load": {
                "type": "number",
                "description": "Minimum cooling_rate to include (filters low-load noise). Default: 50 RT for efficiency charts.",
            },
        },
        "required": ["device_id", "datapoints", "start_time", "end_time"],
    },
}

QUERY_REALTIME_TOOL = {
    "name": "query_realtime",
    "description": """Query current/latest sensor values.
Use this for real-time dashboards or current equipment status.
Returns the most recent value for each datapoint.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "device_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of device IDs to query. Empty array = all devices.",
            },
        },
        "required": [],
    },
}

AGGREGATE_DATA_TOOL = {
    "name": "aggregate_data",
    "description": """Perform aggregations on timeseries data.
Use for calculating statistics like hourly averages, daily totals, peak values.
Returns aggregated data grouped by the specified time bucket.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "device_id": {"type": "string", "description": "Device ID"},
            "datapoint": {"type": "string", "description": "Single datapoint to aggregate"},
            "start_time": {"type": "string", "description": "Start time"},
            "end_time": {"type": "string", "description": "End time"},
            "aggregation": {
                "type": "string",
                "enum": ["avg", "sum", "min", "max", "count"],
                "description": "Aggregation function",
            },
            "group_by": {
                "type": "string",
                "enum": ["hour", "day", "week", "month", "hour_of_day"],
                "description": "Time bucket for grouping. 'hour_of_day' groups by hour across all days.",
            },
        },
        "required": ["device_id", "datapoint", "start_time", "end_time", "aggregation", "group_by"],
    },
}

BATCH_QUERY_TIMESERIES_TOOL = {
    "name": "batch_query_timeseries",
    "description": """Query the SAME datapoints from MULTIPLE devices in ONE call.
Use this instead of multiple query_timeseries calls when fetching the same metric from many devices.

MUCH faster than calling query_timeseries multiple times!

Example: Get status_read from all chillers in one call:
  batch_query_timeseries(
    device_ids=["chiller_1", "chiller_2", "chiller_3", "chiller_4"],
    datapoints=["status_read"],
    start_time="7d",
    end_time="now"
  )

Returns data with device_id field so you can identify which device each row belongs to.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "device_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of device IDs to query (e.g., ['chiller_1', 'chiller_2', 'chiller_3'])",
            },
            "datapoints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Datapoints to fetch from ALL devices (e.g., ['status_read'])",
            },
            "start_time": {
                "type": "string",
                "description": "Start time - either ISO 8601 or relative like '7d', '24h'",
            },
            "end_time": {
                "type": "string",
                "description": "End time - ISO 8601 or 'now'",
            },
            "resample": {
                "type": "string",
                "enum": ["1m", "5m", "15m", "1h", "1d"],
                "description": "Resampling interval",
                "default": "15m",
            },
        },
        "required": ["device_ids", "datapoints", "start_time", "end_time"],
    },
}

LIST_AVAILABLE_DATAPOINTS_TOOL = {
    "name": "list_available_datapoints",
    "description": """List available device types and their datapoints.
Shows device naming patterns (e.g., chiller_{N} means chiller_1, chiller_2, etc.)
Use the exact device IDs from the user's prompt when querying.
Example: "compare chiller_1 and chiller_2" -> use device_ids=["chiller_1", "chiller_2"]""",
    "input_schema": {
        "type": "object",
        "properties": {
            "device_type": {
                "type": "string",
                "enum": ["all", "chiller", "pump", "cooling_tower", "plant", "weather", "chilled_water_loop", "condenser_water_loop"],
                "description": "Filter by device type",
            },
        },
        "required": [],
    },
}


def _parse_relative_time(time_str: str) -> datetime:
    """Parse relative time string like '7d', '24h', '1h' to datetime."""
    now = datetime.now(timezone.utc)

    if time_str == "now":
        return now

    # Try to parse as ISO timestamp first
    try:
        return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    except ValueError:
        pass

    # Parse relative time
    time_str = time_str.strip().lower()
    if time_str.endswith("d"):
        days = int(time_str[:-1])
        return now - timedelta(days=days)
    elif time_str.endswith("h"):
        hours = int(time_str[:-1])
        return now - timedelta(hours=hours)
    elif time_str.endswith("m"):
        minutes = int(time_str[:-1])
        return now - timedelta(minutes=minutes)
    elif time_str.endswith("w"):
        weeks = int(time_str[:-1])
        return now - timedelta(weeks=weeks)

    raise ValueError(f"Cannot parse time: {time_str}")


async def execute_query_timeseries(
    site_id: str,
    device_id: str,
    datapoints: List[str],
    start_time: str,
    end_time: str,
    resample: Optional[str] = None,
    filter_outliers: bool = True,
    min_load: Optional[float] = None,
) -> Dict[str, Any]:
    """Execute timeseries query and return data with outlier filtering.

    Returns:
        Dict with structure:
        {
            "device_id": "plant",
            "datapoints": ["power", "cooling_rate"],
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-07T00:00:00Z",
            "row_count": 168,
            "filter_stats": {"original_count": 200, "removed_count": 32, ...},
            "data": [
                {"timestamp": "...", "power": 150.5, "cooling_rate": 200.0},
                ...
            ]
        }
    """
    try:
        start_dt = _parse_relative_time(start_time)
        end_dt = _parse_relative_time(end_time)

        timescale = await get_timescale(site_id)
        if not timescale.is_connected:
            return {"error": f"Database not connected for site {site_id}"}

        rows = await timescale.query_timeseries(
            device_id=device_id,
            datapoints=datapoints,
            start_time=start_dt,
            end_time=end_dt,
            resample=resample,
        )

        # Pivot rows: {timestamp -> {datapoint -> value}}
        pivoted: Dict[datetime, Dict[str, float]] = {}
        for row in rows:
            ts = row["timestamp"]
            dp = row["datapoint"]
            val = row["value"]
            if ts not in pivoted:
                pivoted[ts] = {}
            pivoted[ts][dp] = val

        # Convert to list of records
        data = []
        for ts in sorted(pivoted.keys()):
            record = {"timestamp": ts.isoformat()}
            record.update(pivoted[ts])
            data.append(record)

        filter_stats = None

        # Apply min_load filter (for efficiency charts, filter low-load noise)
        if min_load is not None and "cooling_rate" in datapoints:
            original_count = len(data)
            data = [r for r in data if r.get("cooling_rate", 0) >= min_load]
            filter_stats = {
                "min_load_filter": min_load,
                "removed_by_min_load": original_count - len(data),
            }

        # Apply outlier filtering
        if filter_outliers and data:
            data, outlier_stats = _apply_outlier_filter(
                data=data,
                datapoints=datapoints,
                method="both",  # Use both IQR and HVAC bounds
                iqr_multiplier=1.5,
                use_hvac_bounds=True,
            )
            if filter_stats:
                filter_stats.update(outlier_stats)
            else:
                filter_stats = outlier_stats

        result = {
            "device_id": device_id,
            "datapoints": datapoints,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "row_count": len(data),
            "data": data,
        }

        if filter_stats:
            result["filter_stats"] = filter_stats

        return result

    except Exception as e:
        logger.error(f"query_timeseries failed: {e}")
        return {"error": str(e)}


async def execute_query_realtime(
    site_id: str,
    device_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Execute realtime query and return latest values.

    Returns:
        Dict with structure:
        {
            "timestamp": "2024-01-15T10:30:00Z",
            "devices": {
                "plant": {"power": 186.5, "cooling_rate": 250.0},
                "chiller_1": {"status_read": 1, "power": 95.2},
                ...
            }
        }
    """
    try:
        # Try Supabase first
        site = get_site_by_id(site_id)
        if site and site.has_supabase:
            supabase = await get_supabase(site_id)
            if supabase.is_connected:
                all_data = await supabase.get_latest_data()
                if all_data:
                    # Filter by device_ids if specified
                    if device_ids:
                        all_data = {
                            d: v for d, v in all_data.items() if d in device_ids
                        }

                    # Simplify structure (remove updated_at for cleaner output)
                    devices = {}
                    for device_id, datapoints in all_data.items():
                        devices[device_id] = {
                            dp: info.get("value") for dp, info in datapoints.items()
                        }

                    return {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "devices": devices,
                    }

        # Fallback to TimescaleDB
        timescale = await get_timescale(site_id)
        if timescale.is_connected:
            rows = await timescale.query_latest()

            # Group by device
            devices: Dict[str, Dict[str, float]] = {}
            for row in rows:
                device_id = row["device_id"]
                if device_ids and device_id not in device_ids:
                    continue
                if device_id not in devices:
                    devices[device_id] = {}
                devices[device_id][row["datapoint"]] = row["value"]

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "devices": devices,
            }

        return {"error": f"No data source available for site {site_id}"}

    except Exception as e:
        logger.error(f"query_realtime failed: {e}")
        return {"error": str(e)}


async def execute_aggregate_data(
    site_id: str,
    device_id: str,
    datapoint: str,
    start_time: str,
    end_time: str,
    aggregation: str,
    group_by: str,
) -> Dict[str, Any]:
    """Execute aggregation query.

    Returns:
        Dict with structure for group_by="hour_of_day":
        {
            "device_id": "plant",
            "datapoint": "power",
            "aggregation": "avg",
            "group_by": "hour_of_day",
            "data": [
                {"hour": 0, "value": 150.2},
                {"hour": 1, "value": 145.8},
                ...
            ]
        }
    """
    try:
        start_dt = _parse_relative_time(start_time)
        end_dt = _parse_relative_time(end_time)

        timescale = await get_timescale(site_id)
        if not timescale.is_connected:
            return {"error": f"Database not connected for site {site_id}"}

        # Fetch raw data first
        rows = await timescale.query_timeseries(
            device_id=device_id,
            datapoints=[datapoint],
            start_time=start_dt,
            end_time=end_dt,
            resample="1h" if group_by in ["hour", "hour_of_day", "day"] else None,
        )

        if not rows:
            return {
                "device_id": device_id,
                "datapoint": datapoint,
                "aggregation": aggregation,
                "group_by": group_by,
                "data": [],
            }

        # Group and aggregate in memory
        from collections import defaultdict

        groups: Dict[Any, List[float]] = defaultdict(list)

        for row in rows:
            ts = row["timestamp"]
            val = row["value"]
            if val is None:
                continue

            if group_by == "hour_of_day":
                key = ts.hour
            elif group_by == "hour":
                key = ts.replace(minute=0, second=0, microsecond=0)
            elif group_by == "day":
                key = ts.date()
            elif group_by == "week":
                key = ts.isocalendar()[:2]  # (year, week)
            elif group_by == "month":
                key = (ts.year, ts.month)
            else:
                key = ts

            groups[key].append(val)

        # Apply aggregation
        agg_funcs = {
            "avg": lambda x: sum(x) / len(x) if x else 0,
            "sum": sum,
            "min": min,
            "max": max,
            "count": len,
        }
        agg_func = agg_funcs.get(aggregation, agg_funcs["avg"])

        data = []
        for key in sorted(groups.keys()):
            values = groups[key]
            agg_value = agg_func(values)

            if group_by == "hour_of_day":
                data.append({"hour": key, "value": round(agg_value, 2)})
            elif group_by == "hour":
                data.append({"timestamp": key.isoformat(), "value": round(agg_value, 2)})
            elif group_by == "day":
                data.append({"date": key.isoformat(), "value": round(agg_value, 2)})
            elif group_by == "week":
                data.append({"year": key[0], "week": key[1], "value": round(agg_value, 2)})
            elif group_by == "month":
                data.append({"year": key[0], "month": key[1], "value": round(agg_value, 2)})

        return {
            "device_id": device_id,
            "datapoint": datapoint,
            "aggregation": aggregation,
            "group_by": group_by,
            "row_count": len(data),
            "data": data,
        }

    except Exception as e:
        logger.error(f"aggregate_data failed: {e}")
        return {"error": str(e)}


async def execute_batch_query_timeseries(
    site_id: str,
    device_ids: List[str],
    datapoints: List[str],
    start_time: str,
    end_time: str,
    resample: str = "15m",
) -> Dict[str, Any]:
    """Query multiple devices in parallel and return combined data.

    Returns:
        Dict with device_id tagged in each record for easy grouping.
    """
    import asyncio

    logger.info(f"[BATCH_QUERY] Querying {len(device_ids)} devices: {device_ids}")
    logger.info(f"[BATCH_QUERY] Datapoints: {datapoints}, Time: {start_time} to {end_time}")

    # Query all devices in parallel
    async def query_device(device_id: str) -> Dict[str, Any]:
        result = await execute_query_timeseries(
            site_id=site_id,
            device_id=device_id,
            datapoints=datapoints,
            start_time=start_time,
            end_time=end_time,
            resample=resample,
            filter_outliers=False,  # Don't filter for status queries
        )
        # Tag each record with device_id
        if "data" in result:
            for record in result["data"]:
                record["device_id"] = device_id
        return result

    results = await asyncio.gather(*[query_device(d) for d in device_ids])

    # Combine all data
    all_data = []
    total_rows = 0
    errors = []

    for device_id, result in zip(device_ids, results):
        if "error" in result:
            errors.append(f"{device_id}: {result['error']}")
        else:
            data = result.get("data", [])
            all_data.extend(data)
            total_rows += len(data)

    logger.info(f"[BATCH_QUERY] Total rows: {total_rows}, Errors: {len(errors)}")

    return {
        "device_ids": device_ids,
        "datapoints": datapoints,
        "start_time": start_time,
        "end_time": end_time,
        "total_rows": total_rows,
        "data": all_data,
        "errors": errors if errors else None,
    }


async def execute_list_available_datapoints(
    site_id: str,
    device_type: Optional[str] = None,
) -> Dict[str, Any]:
    """List available devices and datapoints.

    Returns:
        Dict with structure:
        {
            "devices": {
                "plant": {
                    "type": "plant",
                    "datapoints": ["power", "cooling_rate", "efficiency"]
                },
                "chiller_1": {
                    "type": "chiller",
                    "datapoints": ["power", "percentage_rla", "evap_lwt", "cond_ewt"]
                },
                ...
            }
        }
    """
    # Define device type patterns and their datapoints
    # Use patterns like "chiller_{N}" - AI should use exact device IDs from user prompt
    # e.g., "compare chiller_1 and chiller_2" -> query device_ids: ["chiller_1", "chiller_2"]
    device_types = {
        "plant": {
            "pattern": "plant",
            "description": "Overall plant aggregate data",
            "datapoints": [
                "cooling_rate",
                "cumulative_cooling_energy",
                "cumulative_energy",
                "efficiency",
                "efficiency_annual",
                "efficiency_cdp",
                "efficiency_chiller",
                "efficiency_ct",
                "efficiency_pchp",
                "heat_balance",
                "heat_reject",
                "number_of_running_cdps",
                "number_of_running_chillers",
                "number_of_running_cts",
                "number_of_running_pchps",
                "power",
                "power_all_cdps",
                "power_all_chillers",
                "power_all_cts",
                "power_all_pchps",
                "running_capacity",
                "target_cdw_setpoint",
                "target_chw_setpoint"
            ],
        },
        "chiller": {
            "pattern": "chiller_{N}",
            "description": "Individual chillers (chiller_1, chiller_2, chiller_3, etc.)",
            "datapoints": [
                "alarm",
                "compressor_runtime",
                "cond_approach_temperature",
                "cond_delta_temperature",
                "cond_entering_water_temperature",
                "cond_leaving_water_temperature",
                "cond_sat_refrig_pressure",
                "cond_sat_refrig_temperature",
                "cond_water_flow_rate",
                "cond_water_flow_status",
                "cooling_rate",
                "cumulative_energy",
                "current_average",
                "current_l1",
                "current_l2",
                "current_l3",
                "demand_limit_setpoint_local",
                "demand_limit_setpoint_read",
                "demand_limit_setpoint_write",
                "efficiency",
                "evap_approach_temperature",
                "evap_delta_temperature",
                "evap_entering_water_temperature",
                "evap_leaving_water_temperature",
                "evap_sat_refrig_pressure",
                "evap_sat_refrig_temperature",
                "evap_water_flow_rate",
                "evap_water_flow_status",
                "heat_balance",
                "heat_reject",
                "mode",
                "oil_diff_pressure",
                "oil_pump_disc_temperature",
                "oil_tank_pressure",
                "oil_tank_temperature",
                "percentage_rla",
                "power",
                "power_factor",
                "running_capacity",
                "setpoint_local",
                "setpoint_read",
                "setpoint_write",
                "status_local",
                "status_read",
                "status_write",
                "voltage_l1l2",
                "voltage_l2l3",
                "voltage_l3l1",
                "voltage_ll_average"
            ],
        },
        "chilled_water_loop": {
            "pattern": "chilled_water_loop",
            "description": "Chilled water loop",
            "datapoints": ["supply_water_temperature", "return_water_temperature", "flow_rate", "water_delta_temperature"],
        },
        "condenser_water_loop": {
            "pattern": "condenser_water_loop",
            "description": "Condenser water loop",
            "datapoints": ["supply_water_temperature", "return_water_temperature", "flow_rate", "water_delta_temperature"],
        },
        "ct": {
            "pattern": "ct_{N}",
            "description": "Cooling towers (cooling_tower_1, cooling_tower_2, etc.)",
            "datapoints": ["alarm", "status_read"],
        },
        "weather": {
            "pattern": "outdoor_weather_station",
            "description": "Outdoor weather station",
            "datapoints": ["drybulb_temperature", "wetbulb_temperature", "humidity"],
        },
        "pump": {
            "pattern": "pchp_{N}, schp_{N}, cdp_{N}",
            "description": "Pumps - primary (pchp), secondary (schp), condenser (cdp)",
            "datapoints": ["status_read", "efficiency", "power", "alarm", "freqeuncy_read"],
        },
    }

    # Filter by device type
    if device_type and device_type != "all":
        filtered = {
            d: info
            for d, info in device_types.items()
            if d == device_type
        }
    else:
        filtered = device_types

    return {"device_types": filtered}


# Map tool names to executors
TOOL_EXECUTORS = {
    "query_timeseries": execute_query_timeseries,
    "batch_query_timeseries": execute_batch_query_timeseries,
    "query_realtime": execute_query_realtime,
    "aggregate_data": execute_aggregate_data,
    "list_available_datapoints": execute_list_available_datapoints,
}

# All data tool definitions
DATA_TOOLS = [
    QUERY_TIMESERIES_TOOL,
    BATCH_QUERY_TIMESERIES_TOOL,  # For querying multiple devices at once
    QUERY_REALTIME_TOOL,
    AGGREGATE_DATA_TOOL,
    LIST_AVAILABLE_DATAPOINTS_TOOL,
]
