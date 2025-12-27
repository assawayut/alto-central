"""Energy data API endpoints.

These endpoints provide energy consumption summaries.
Each site can have its own database configured in sites.yaml.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import APIRouter, Path

from app.db.connections import get_timescale
from app.config import get_site_by_id
from app.models.schemas.energy import EnergyValues, EnergyDailyResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/daily",
    response_model=EnergyDailyResponse,
    summary="Get daily energy comparison",
    description="Compare yesterday's energy usage with today's (so far).",
)
async def get_daily_energy(
    site_id: str = Path(..., description="Site identifier"),
) -> EnergyDailyResponse:
    """Get daily energy comparison (yesterday vs today).

    Calculates energy from power readings integrated over time.
    Returns null values if data is not available.
    """
    # Get site-specific TimescaleDB connection
    timescale = await get_timescale(site_id)

    if not timescale.is_connected:
        return EnergyDailyResponse(
            site_id=site_id,
            yesterday=EnergyValues(total=None, plant=None, air_side=None),
            today=EnergyValues(total=None, plant=None, air_side=None),
            unit="kWh",
        )

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    yesterday_end = today_start

    # Query yesterday's energy from aggregated_data
    energy_query = """
        SELECT
            SUM(value) / 60.0 as energy_kwh  -- Assuming 1-minute samples
        FROM aggregated_data
        WHERE site_id = $1
          AND device_id = 'plant'
          AND datapoint = 'power'
          AND timestamp >= $2
          AND timestamp < $3
    """

    try:
        yesterday_result = await timescale.fetch(
            energy_query, site_id, yesterday_start, yesterday_end
        )
        today_result = await timescale.fetch(
            energy_query, site_id, today_start, now
        )

        yesterday_plant = (
            yesterday_result[0]["energy_kwh"]
            if yesterday_result and yesterday_result[0]["energy_kwh"]
            else None
        )
        today_plant = (
            today_result[0]["energy_kwh"]
            if today_result and today_result[0]["energy_kwh"]
            else None
        )

        # Check site HVAC type from config
        site = get_site_by_id(site_id)
        hvac_type = site.hvac_type if site else "water"

        # For water-only sites, plant IS the total (no air-side)
        # For sites with air-side, we would query air-side separately
        if hvac_type == "water":
            # Water-side only: plant power is the total, no air-side
            return EnergyDailyResponse(
                site_id=site_id,
                yesterday=EnergyValues(
                    total=yesterday_plant,
                    plant=yesterday_plant,
                    air_side=None,
                ),
                today=EnergyValues(
                    total=today_plant,
                    plant=today_plant,
                    air_side=None,
                ),
                unit="kWh",
            )
        else:
            # TODO: Query air-side energy separately for sites with air-side HVAC
            # For now, just return plant energy
            return EnergyDailyResponse(
                site_id=site_id,
                yesterday=EnergyValues(
                    total=yesterday_plant,
                    plant=yesterday_plant,
                    air_side=None,
                ),
                today=EnergyValues(
                    total=today_plant,
                    plant=today_plant,
                    air_side=None,
                ),
                unit="kWh",
            )
    except Exception as e:
        logger.error(f"Energy query failed for site {site_id}: {e}")
        return EnergyDailyResponse(
            site_id=site_id,
            yesterday=EnergyValues(total=None, plant=None, air_side=None),
            today=EnergyValues(total=None, plant=None, air_side=None),
            unit="kWh",
        )


@router.get(
    "/monthly",
    summary="Get monthly energy summary",
    description="Get energy consumption for the current and previous month.",
)
async def get_monthly_energy(
    site_id: str = Path(..., description="Site identifier"),
) -> Dict:
    """Get monthly energy summary.

    Returns null values when data is not available.
    """
    # TODO: Implement actual query from daily_energy_data table
    # For now, return null values to indicate no data
    return {
        "site_id": site_id,
        "current_month": {
            "month": datetime.utcnow().strftime("%Y-%m"),
            "total_kwh": None,
            "days_elapsed": datetime.utcnow().day,
            "projected_kwh": None,
        },
        "previous_month": {
            "month": (datetime.utcnow().replace(day=1) - timedelta(days=1)).strftime("%Y-%m"),
            "total_kwh": None,
        },
        "year_to_date": {
            "total_kwh": None,
            "average_monthly_kwh": None,
        },
    }
