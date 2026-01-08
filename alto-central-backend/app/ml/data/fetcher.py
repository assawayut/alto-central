"""Data fetching layer for ML training.

Fetches historical data from TimescaleDB for model training.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from app.db.connections import get_timescale
from app.core import get_table_for_resolution

logger = logging.getLogger(__name__)


@dataclass
class ChillerTrainingData:
    """Training data structure for a single chiller."""

    chiller_id: str
    site_id: str
    timestamps: List[datetime]
    power: List[float]  # kW
    percentage_rla: List[float]  # %
    evap_lwt: List[float]  # Evaporator Leaving Water Temp (°F)
    evap_ewt: List[float]  # Evaporator Entering Water Temp (°F)
    cond_lwt: List[float]  # Condenser Leaving Water Temp (°F)
    cond_ewt: List[float]  # Condenser Entering Water Temp (°F)
    status: List[int]  # 0/1
    cooling_load: List[float]  # RT (from plant)
    chs: List[float]  # Chilled water supply temp (°F)
    cds: List[float]  # Condenser water supply temp (°F)

    def to_dataframe(self) -> "pd.DataFrame":
        """Convert to pandas DataFrame for model training."""
        if not HAS_PANDAS:
            raise ImportError("pandas is required for to_dataframe()")

        return pd.DataFrame(
            {
                "timestamp": self.timestamps,
                "power": self.power,
                "percentage_rla": self.percentage_rla,
                "evap_lwt": self.evap_lwt,
                "evap_ewt": self.evap_ewt,
                "cond_lwt": self.cond_lwt,
                "cond_ewt": self.cond_ewt,
                "status": self.status,
                "cooling_load": self.cooling_load,
                "chs": self.chs,
                "cds": self.cds,
            }
        )


class MLDataFetcher:
    """Fetches and prepares data for ML model training and inference."""

    def __init__(self, site_id: str):
        """Initialize data fetcher.

        Args:
            site_id: Site identifier
        """
        self.site_id = site_id

    async def fetch_chiller_training_data(
        self,
        chiller_id: str,
        start_date: datetime,
        end_date: datetime,
        resolution: str = "15m",
    ) -> ChillerTrainingData:
        """Fetch training data for a specific chiller.

        Args:
            chiller_id: Chiller device ID (e.g., "chiller_1")
            start_date: Start of training period
            end_date: End of training period
            resolution: Data resolution ("1m", "15m", "1h")

        Returns:
            ChillerTrainingData with all required fields
        """
        timescale = await get_timescale(self.site_id)
        table_name = get_table_for_resolution(resolution)

        # Query chiller-specific data
        chiller_query = f"""
            SELECT timestamp, datapoint, value
            FROM {table_name}
            WHERE site_id = $1
              AND device_id = $2
              AND datapoint IN (
                  'power', 'percentage_rla', 'status_read',
                  'evap_leaving_water_temperature', 'evap_entering_water_temperature',
                  'cond_leaving_water_temperature', 'cond_entering_water_temperature'
              )
              AND timestamp >= $3
              AND timestamp < $4
            ORDER BY timestamp
        """

        # Query loop temperatures
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

        # Query plant cooling load
        cooling_load_query = f"""
            SELECT timestamp, value
            FROM {table_name}
            WHERE site_id = $1
              AND device_id = 'plant'
              AND datapoint = 'cooling_rate'
              AND timestamp >= $2
              AND timestamp < $3
            ORDER BY timestamp
        """

        # Execute all queries
        chiller_rows = await timescale.fetch(
            chiller_query, self.site_id, chiller_id, start_date, end_date
        )
        chs_rows = await timescale.fetch(chs_query, self.site_id, start_date, end_date)
        cds_rows = await timescale.fetch(cds_query, self.site_id, start_date, end_date)
        cooling_load_rows = await timescale.fetch(
            cooling_load_query, self.site_id, start_date, end_date
        )

        # Convert to lookup dicts by timestamp
        chs_lookup = {row["timestamp"]: row["value"] for row in chs_rows}
        cds_lookup = {row["timestamp"]: row["value"] for row in cds_rows}
        cooling_load_lookup = {
            row["timestamp"]: row["value"] for row in cooling_load_rows
        }

        # Pivot chiller data by timestamp
        chiller_data: Dict[datetime, Dict[str, float]] = {}
        for row in chiller_rows:
            ts = row["timestamp"]
            if ts not in chiller_data:
                chiller_data[ts] = {}
            chiller_data[ts][row["datapoint"]] = row["value"]

        # Build result arrays
        timestamps = []
        power = []
        percentage_rla = []
        evap_lwt = []
        evap_ewt = []
        cond_lwt = []
        cond_ewt = []
        status = []
        cooling_load = []
        chs = []
        cds = []

        for ts in sorted(chiller_data.keys()):
            data = chiller_data[ts]

            # Skip if missing critical data
            if "power" not in data or "status_read" not in data:
                continue

            timestamps.append(ts)
            power.append(data.get("power", 0.0))
            percentage_rla.append(data.get("percentage_rla", 0.0))
            evap_lwt.append(data.get("evap_leaving_water_temperature", 0.0))
            evap_ewt.append(data.get("evap_entering_water_temperature", 0.0))
            cond_lwt.append(data.get("cond_leaving_water_temperature", 0.0))
            cond_ewt.append(data.get("cond_entering_water_temperature", 0.0))
            status.append(int(data.get("status_read", 0)))
            cooling_load.append(cooling_load_lookup.get(ts, 0.0))
            chs.append(chs_lookup.get(ts, 0.0))
            cds.append(cds_lookup.get(ts, 0.0))

        logger.info(
            f"Fetched {len(timestamps)} data points for {chiller_id} "
            f"from {start_date} to {end_date}"
        )

        return ChillerTrainingData(
            chiller_id=chiller_id,
            site_id=self.site_id,
            timestamps=timestamps,
            power=power,
            percentage_rla=percentage_rla,
            evap_lwt=evap_lwt,
            evap_ewt=evap_ewt,
            cond_lwt=cond_lwt,
            cond_ewt=cond_ewt,
            status=status,
            cooling_load=cooling_load,
            chs=chs,
            cds=cds,
        )

    async def fetch_combination_training_data(
        self,
        chiller_ids: List[str],
        start_date: datetime,
        end_date: datetime,
        resolution: str = "15m",
    ) -> "pd.DataFrame":
        """Fetch training data for a specific chiller combination.

        Filters to only timestamps where exactly these chillers are running.

        Args:
            chiller_ids: List of chiller IDs (e.g., ["chiller_1", "chiller_2"])
            start_date: Start of training period
            end_date: End of training period
            resolution: Data resolution

        Returns:
            DataFrame with combined data for the chiller combination
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required for combination training data")

        timescale = await get_timescale(self.site_id)
        table_name = get_table_for_resolution(resolution)

        # First, get all chiller status data
        all_chillers = await self.get_available_chillers()

        # Query status for all chillers
        status_query = f"""
            SELECT timestamp, device_id, value
            FROM {table_name}
            WHERE site_id = $1
              AND device_id = ANY($2)
              AND datapoint = 'status_read'
              AND timestamp >= $3
              AND timestamp < $4
            ORDER BY timestamp
        """

        status_rows = await timescale.fetch(
            status_query, self.site_id, all_chillers, start_date, end_date
        )

        # Build status lookup: timestamp -> {chiller_id: status}
        status_by_ts: Dict[datetime, Dict[str, int]] = {}
        for row in status_rows:
            ts = row["timestamp"]
            if ts not in status_by_ts:
                status_by_ts[ts] = {}
            status_by_ts[ts][row["device_id"]] = int(row["value"])

        # Find timestamps where exactly the specified chillers are running
        target_set = set(chiller_ids)
        valid_timestamps = []

        for ts, statuses in status_by_ts.items():
            running_chillers = {
                ch for ch, status in statuses.items() if status >= 1
            }
            if running_chillers == target_set:
                valid_timestamps.append(ts)

        if not valid_timestamps:
            logger.warning(
                f"No data found for combination {'+'.join(chiller_ids)}"
            )
            return pd.DataFrame()

        logger.info(
            f"Found {len(valid_timestamps)} timestamps for combination "
            f"{'+'.join(chiller_ids)}"
        )

        # Query plant-level data for valid timestamps
        plant_query = f"""
            SELECT timestamp, datapoint, value
            FROM {table_name}
            WHERE site_id = $1
              AND device_id = 'plant'
              AND datapoint IN ('power_all_chillers', 'cooling_rate')
              AND timestamp = ANY($2)
            ORDER BY timestamp
        """

        plant_rows = await timescale.fetch(
            plant_query, self.site_id, valid_timestamps
        )

        # Query loop temperatures
        loop_query = f"""
            SELECT timestamp, device_id, datapoint, value
            FROM {table_name}
            WHERE site_id = $1
              AND device_id IN ('chilled_water_loop', 'condenser_water_loop')
              AND datapoint = 'supply_water_temperature'
              AND timestamp = ANY($2)
            ORDER BY timestamp
        """

        loop_rows = await timescale.fetch(loop_query, self.site_id, valid_timestamps)

        # Build result DataFrame
        data: Dict[datetime, Dict[str, float]] = {}

        for ts in valid_timestamps:
            data[ts] = {"timestamp": ts}

        for row in plant_rows:
            ts = row["timestamp"]
            if ts in data:
                if row["datapoint"] == "power_all_chillers":
                    data[ts]["power"] = row["value"]
                elif row["datapoint"] == "cooling_rate":
                    data[ts]["cooling_load"] = row["value"]

        for row in loop_rows:
            ts = row["timestamp"]
            if ts in data:
                if row["device_id"] == "chilled_water_loop":
                    data[ts]["evap_lwt"] = row["value"]
                    data[ts]["chs"] = row["value"]
                elif row["device_id"] == "condenser_water_loop":
                    data[ts]["cond_ewt"] = row["value"]
                    data[ts]["cds"] = row["value"]

        # Convert to DataFrame
        df = pd.DataFrame(list(data.values()))

        if df.empty:
            return df

        # Fill missing columns
        for col in ["power", "cooling_load", "evap_lwt", "cond_ewt", "chs", "cds"]:
            if col not in df.columns:
                df[col] = 0.0

        return df

    async def get_available_chillers(self) -> List[str]:
        """Get list of chiller device_ids at this site.

        Returns:
            List of chiller device IDs (e.g., ["chiller_1", "chiller_2"])
        """
        timescale = await get_timescale(self.site_id)

        query = """
            SELECT DISTINCT device_id
            FROM aggregated_data_1hour
            WHERE site_id = $1
              AND device_id LIKE 'chiller_%'
              AND datapoint = 'status_read'
            ORDER BY device_id
        """

        rows = await timescale.fetch(query, self.site_id)
        return [row["device_id"] for row in rows]

    async def get_chiller_combinations_in_data(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Tuple[str, ...]]:
        """Identify which chiller combinations exist in the data.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            List of tuples, each containing chiller IDs that run together
        """
        timescale = await get_timescale(self.site_id)
        all_chillers = await self.get_available_chillers()

        # Query status for all chillers
        query = """
            SELECT timestamp, device_id, value
            FROM aggregated_data_1hour
            WHERE site_id = $1
              AND device_id = ANY($2)
              AND datapoint = 'status_read'
              AND timestamp >= $3
              AND timestamp < $4
            ORDER BY timestamp
        """

        rows = await timescale.fetch(
            query, self.site_id, all_chillers, start_date, end_date
        )

        # Build combinations
        combinations: set = set()
        status_by_ts: Dict[datetime, Dict[str, int]] = {}

        for row in rows:
            ts = row["timestamp"]
            if ts not in status_by_ts:
                status_by_ts[ts] = {}
            status_by_ts[ts][row["device_id"]] = int(row["value"])

        for ts, statuses in status_by_ts.items():
            running = tuple(
                sorted(ch for ch, status in statuses.items() if status >= 1)
            )
            if running:
                combinations.add(running)

        return sorted(combinations, key=lambda x: (len(x), x))
