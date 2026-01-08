"""TimescaleDB connection manager for historical data (READ-ONLY).

This module provides READ-ONLY connections to production TimescaleDB databases.
Each site can have its own TimescaleDB instance configured in sites.yaml.

Configuration is loaded per-site from config/sites.yaml.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, List, Optional
import logging

from app.config.sites import get_site_timescale_config, TimescaleConfig
from app.core.exceptions import ExternalServiceException

logger = logging.getLogger(__name__)


class TimescaleConnection:
    """READ-ONLY connection to a site's TimescaleDB instance.

    All queries are executed with READ-ONLY transaction mode to prevent
    any accidental writes to the production database.
    """

    def __init__(self, site_id: str, config: TimescaleConfig):
        self.site_id = site_id
        self.host = config.host
        self.port = config.port
        self.database = config.database
        self.user = config.user
        self.password = config.password
        self.ssl_mode = config.ssl_mode
        self._pool = None
        self._connected = False

    async def connect(self) -> None:
        """Initialize the connection pool."""
        if not self.host or not self.password:
            logger.warning(f"TimescaleDB not configured for site {self.site_id}, using mock mode")
            self._connected = False
            return

        try:
            import asyncpg
            import ssl as ssl_module

            # Configure SSL based on ssl_mode
            ssl_context = None
            if self.ssl_mode == "require":
                ssl_context = ssl_module.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl_module.CERT_NONE
            elif self.ssl_mode == "verify-full":
                ssl_context = ssl_module.create_default_context()
            # ssl_mode == "disable" -> ssl_context = None

            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                ssl=ssl_context,
                min_size=2,
                max_size=10,
                command_timeout=30.0,  # 30 second timeout for queries
                # Set default transaction to read-only for safety
                server_settings={
                    "default_transaction_read_only": "on",
                    "statement_timeout": "30000",  # 30 second statement timeout (ms)
                },
            )
            self._connected = True
            logger.info(f"Connected to TimescaleDB at {self.host}:{self.port} for site {self.site_id} (READ-ONLY)")
        except Exception as e:
            logger.error(f"Failed to connect to TimescaleDB for site {self.site_id}: {e}")
            self._connected = False

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._connected = False
            logger.info(f"Closed TimescaleDB connection for site {self.site_id}")

    @property
    def is_connected(self) -> bool:
        return self._connected and self._pool is not None

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator:
        """Get a read-only connection from the pool."""
        if not self.is_connected:
            raise ExternalServiceException(
                "TimescaleDB", f"Not connected to database for site {self.site_id}"
            )

        async with self._pool.acquire() as conn:
            # Ensure read-only mode at connection level
            await conn.execute("SET TRANSACTION READ ONLY")
            yield conn

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a read-only query and return results."""
        if not self.is_connected:
            return self._get_mock_data(query, *args)

        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"TimescaleDB query error for site {self.site_id}: {e}")
            raise ExternalServiceException("TimescaleDB", str(e))

    async def fetchval(self, query: str, *args) -> Any:
        """Execute a query and return a single value."""
        if not self.is_connected:
            return None

        try:
            async with self.get_connection() as conn:
                return await conn.fetchval(query, *args)
        except Exception as e:
            logger.error(f"TimescaleDB query error for site {self.site_id}: {e}")
            raise ExternalServiceException("TimescaleDB", str(e))

    async def query_timeseries(
        self,
        device_id: str,
        datapoints: List[str],
        start_time: datetime,
        end_time: datetime,
        resample: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query timeseries data from aggregated_data with optional resampling.

        Args:
            device_id: Device identifier
            datapoints: List of datapoint names
            start_time: Query start time
            end_time: Query end time
            resample: Optional resample interval (e.g., '1 hour', '15 minutes')

        Returns empty list if not connected or query fails.
        """
        if not self.is_connected:
            return []

        try:
            if resample:
                # Use time_bucket for resampling
                # Note: interval is embedded in SQL (safe - values come from resample_map)
                query = f"""
                    SELECT
                        time_bucket(INTERVAL '{resample}', timestamp) as timestamp,
                        device_id,
                        datapoint,
                        AVG(value) as value
                    FROM aggregated_data
                    WHERE site_id = $1
                      AND device_id = $2
                      AND datapoint = ANY($3)
                      AND timestamp >= $4
                      AND timestamp < $5
                    GROUP BY 1, 2, 3
                    ORDER BY timestamp
                """
                return await self.fetch(
                    query, self.site_id, device_id, datapoints,
                    start_time, end_time
                )
            else:
                query = """
                    SELECT timestamp, device_id, datapoint, value
                    FROM aggregated_data
                    WHERE site_id = $1
                      AND device_id = $2
                      AND datapoint = ANY($3)
                      AND timestamp >= $4
                      AND timestamp < $5
                    ORDER BY timestamp
                """
                return await self.fetch(
                    query, self.site_id, device_id, datapoints, start_time, end_time
                )
        except Exception as e:
            logger.error(f"TimescaleDB timeseries query error for site {self.site_id}: {e}")
            return []

    async def query_latest(self, max_age_minutes: int = 60) -> List[Dict[str, Any]]:
        """Query latest values for all devices at this site from aggregated_data.

        This is a fallback when Supabase latest_data is not available.
        Uses the most recent timestamp from aggregated_data table.

        Args:
            max_age_minutes: Only look at data from the last N minutes (default 60)

        Returns empty list if not connected or query fails.
        """
        if not self.is_connected:
            return []

        try:
            # Limit time range for performance - only look at recent data
            query = """
                SELECT DISTINCT ON (device_id, datapoint)
                    device_id, datapoint, value, timestamp as updated_at
                FROM aggregated_data
                WHERE site_id = $1
                  AND timestamp >= NOW() - INTERVAL '%s minutes'
                ORDER BY device_id, datapoint, timestamp DESC
            """ % max_age_minutes
            return await self.fetch(query, self.site_id)
        except Exception as e:
            logger.error(f"TimescaleDB query_latest error for site {self.site_id}: {e}")
            return []

    async def query_daily_energy_data(
        self,
        start_date: datetime,
        end_date: datetime,
        device_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query daily energy data from daily_energy_data table.

        Args:
            start_date: Start date for query
            end_date: End date for query
            device_id: Optional device filter

        Returns empty list if not connected or query fails.
        """
        if not self.is_connected:
            return []

        try:
            if device_id:
                query = """
                    SELECT timestamp, device_id, datapoint, value
                    FROM daily_energy_data
                    WHERE site_id = $1
                      AND device_id = $2
                      AND timestamp >= $3
                      AND timestamp <= $4
                    ORDER BY timestamp
                """
                return await self.fetch(query, self.site_id, device_id, start_date, end_date)
            else:
                query = """
                    SELECT timestamp, device_id, datapoint, value
                    FROM daily_energy_data
                    WHERE site_id = $1
                      AND timestamp >= $2
                      AND timestamp <= $3
                    ORDER BY timestamp, device_id
                """
                return await self.fetch(query, self.site_id, start_date, end_date)
        except Exception as e:
            logger.error(f"TimescaleDB daily_energy_data query error for site {self.site_id}: {e}")
            return []



class TimescaleConnectionManager:
    """Manages TimescaleDB connections for multiple sites.

    Creates and caches connections per site based on config/sites.yaml.
    """

    def __init__(self):
        self._connections: Dict[str, TimescaleConnection] = {}

    async def get_connection(self, site_id: str) -> TimescaleConnection:
        """Get or create a TimescaleDB connection for a site."""
        if site_id not in self._connections:
            config = get_site_timescale_config(site_id)

            if config and config.is_configured:
                conn = TimescaleConnection(site_id, config)
                await conn.connect()
            else:
                # Create a mock connection for sites without TimescaleDB config
                logger.info(f"No TimescaleDB config for site {site_id}, using mock mode")
                conn = TimescaleConnection(site_id, TimescaleConfig())

            self._connections[site_id] = conn

        return self._connections[site_id]

    async def close_all(self) -> None:
        """Close all connections."""
        for conn in self._connections.values():
            await conn.close()
        self._connections.clear()
        logger.info("Closed all TimescaleDB connections")


# Global connection manager
_timescale_manager: Optional[TimescaleConnectionManager] = None


async def init_timescale() -> None:
    """Initialize the global TimescaleDB connection manager."""
    global _timescale_manager
    _timescale_manager = TimescaleConnectionManager()
    logger.info("TimescaleDB connection manager initialized")


async def close_timescale() -> None:
    """Close all TimescaleDB connections."""
    global _timescale_manager
    if _timescale_manager:
        await _timescale_manager.close_all()


def get_timescale_manager() -> TimescaleConnectionManager:
    """Get the TimescaleDB connection manager."""
    if _timescale_manager is None:
        raise RuntimeError("TimescaleDB connection manager not initialized")
    return _timescale_manager


async def get_timescale(site_id: str) -> TimescaleConnection:
    """Get a TimescaleDB connection for a specific site."""
    manager = get_timescale_manager()
    return await manager.get_connection(site_id)
