"""Real-time data API endpoints.

These endpoints provide real-time sensor data.
Primary source: Supabase (if configured)
Fallback: TimescaleDB aggregated_data table (latest timestamp)
Each site can have its own database configured in sites.yaml.
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Path

from app.db.connections import get_supabase, get_timescale
from app.config import get_site_by_id
from app.models.schemas.realtime import (
    RealtimeDataResponse,
    DeviceDataResponse,
)

router = APIRouter()


async def get_realtime_data_for_site(site_id: str) -> Dict[str, Dict[str, Any]]:
    """Get realtime data from Supabase (primary) or TimescaleDB (fallback).

    Priority:
    1. Supabase latest_data table (if configured)
    2. TimescaleDB aggregated_data table with latest timestamp (fallback)
    3. Empty dict if neither available

    Returns nested dict: {device_id: {datapoint: {value, updated_at}}}
    """
    import logging
    logger = logging.getLogger(__name__)

    site = get_site_by_id(site_id)

    # Try Supabase first (primary source for real-time data)
    if site and site.has_supabase:
        try:
            supabase = await get_supabase(site_id)
            if supabase.is_connected:
                data = await supabase.get_latest_data()
                if data:
                    return data
        except Exception as e:
            logger.warning(f"Supabase failed for {site_id}, trying TimescaleDB: {e}")

    # Fallback to TimescaleDB for sites without Supabase
    if site and site.has_timescaledb:
        try:
            timescale = await get_timescale(site_id)
            if timescale.is_connected:
                rows = await timescale.query_latest()
                # Transform flat rows to nested structure
                result: Dict[str, Dict[str, Any]] = {}
                for row in rows:
                    device_id = row["device_id"]
                    datapoint = row["datapoint"]
                    if device_id not in result:
                        result[device_id] = {}
                    result[device_id][datapoint] = {
                        "value": row["value"],
                        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    }
                return result
        except Exception as e:
            logger.error(f"TimescaleDB query failed for {site_id}: {e}")

    # No data source available
    return {}


@router.get(
    "/latest",
    response_model=RealtimeDataResponse,
    summary="Get latest data for all devices",
    description="Fetches the most recent sensor values for all devices at a site.",
)
async def get_latest_data(
    site_id: str = Path(..., description="Site identifier"),
) -> RealtimeDataResponse:
    """Get latest real-time data for all devices at a site.

    Returns a nested structure of device_id -> datapoint -> {value, updated_at}
    """
    devices = await get_realtime_data_for_site(site_id)

    return RealtimeDataResponse(
        site_id=site_id,
        timestamp=datetime.utcnow(),
        devices=devices,
    )


@router.get(
    "/latest/{device_id}",
    response_model=DeviceDataResponse,
    summary="Get latest data for a specific device",
    description="Fetches the most recent sensor values for a specific device.",
)
async def get_device_latest_data(
    site_id: str = Path(..., description="Site identifier"),
    device_id: str = Path(..., description="Device identifier"),
) -> DeviceDataResponse:
    """Get latest real-time data for a specific device."""
    # Get site-specific Supabase connection
    supabase = await get_supabase(site_id)
    datapoints = await supabase.get_device_data(device_id)

    # Transform to proper response format
    formatted_datapoints = {}
    for name, data in datapoints.items():
        formatted_datapoints[name] = {
            "value": data.get("value", 0),
            "updated_at": data.get("updated_at", datetime.utcnow().isoformat()),
        }

    return DeviceDataResponse(
        device_id=device_id,
        datapoints=formatted_datapoints,
    )


@router.get(
    "/plant",
    summary="Get plant-level summary",
    description="Fetches aggregated plant-level metrics.",
)
async def get_plant_summary(
    site_id: str = Path(..., description="Site identifier"),
) -> Dict[str, Any]:
    """Get plant-level summary data."""
    # Get site-specific Supabase connection
    supabase = await get_supabase(site_id)
    devices = await supabase.get_latest_data()

    plant = devices.get("plant", {})
    chw = devices.get("chilled_water_loop", {})
    cdw = devices.get("condenser_water_loop", {})
    weather = devices.get("outdoor_weather_station", {})

    return {
        "site_id": site_id,
        "plant": {
            "power_kw": plant.get("power", {}).get("value", 0),
            "cooling_rate_rt": plant.get("cooling_rate", {}).get("value", 0),
            "efficiency_kw_rt": plant.get("efficiency", {}).get("value", 0),
            "heat_reject_rt": plant.get("heat_reject", {}).get("value", 0),
        },
        "chilled_water": {
            "supply_temp_f": chw.get("supply_water_temperature", {}).get("value", 0),
            "return_temp_f": chw.get("return_water_temperature", {}).get("value", 0),
            "delta_t": (
                chw.get("return_water_temperature", {}).get("value", 0)
                - chw.get("supply_water_temperature", {}).get("value", 0)
            ),
            "flow_rate_gpm": chw.get("flow_rate", {}).get("value", 0),
        },
        "condenser_water": {
            "supply_temp_f": cdw.get("supply_water_temperature", {}).get("value", 0),
            "return_temp_f": cdw.get("return_water_temperature", {}).get("value", 0),
            "delta_t": (
                cdw.get("return_water_temperature", {}).get("value", 0)
                - cdw.get("supply_water_temperature", {}).get("value", 0)
            ),
            "flow_rate_gpm": cdw.get("flow_rate", {}).get("value", 0),
        },
        "weather": {
            "drybulb_temp_f": weather.get("drybulb_temperature", {}).get("value", 0),
            "wetbulb_temp_f": weather.get("wetbulb_temperature", {}).get("value", 0),
            "humidity_pct": weather.get("humidity", {}).get("value", 0),
        },
    }
