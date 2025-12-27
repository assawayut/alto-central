"""Supabase connection manager for real-time data (READ-ONLY).

This module provides READ-ONLY connections to production Supabase databases.
Each site can have its own Supabase instance configured in sites.yaml.

Uses httpx for direct PostgREST API calls to support self-hosted Supabase
instances that may not have SSL configured.

Configuration is loaded per-site from config/sites.yaml.
"""

from typing import Any, Dict, List, Optional
import logging

import httpx

from app.config.sites import get_site_supabase_config, SupabaseConfig
from app.core.exceptions import ExternalServiceException

logger = logging.getLogger(__name__)


class SupabaseConnection:
    """READ-ONLY connection to a site's Supabase instance.

    Uses httpx for direct PostgREST API calls instead of the official
    Supabase client, to support self-hosted instances on HTTP.

    This class provides methods to query real-time sensor data from Supabase.
    All methods are read-only - no insert, update, or delete operations.
    """

    def __init__(self, site_id: str, config: SupabaseConfig):
        self.site_id = site_id
        self.url = config.url.rstrip("/") if config.url else None
        self.api_key = config.api_key
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

    async def connect(self) -> None:
        """Initialize the HTTP client for PostgREST API calls."""
        if not self.url or not self.api_key:
            logger.warning(f"Supabase not configured for site {self.site_id}")
            self._connected = False
            return

        try:
            # Create httpx async client with proper headers for PostgREST
            self._client = httpx.AsyncClient(
                base_url=f"{self.url}/rest/v1",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                timeout=30.0,
            )
            self._connected = True
            logger.info(f"Connected to Supabase PostgREST at {self.url} for site {self.site_id} (READ-ONLY)")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase for site {self.site_id}: {e}")
            self._connected = False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None

    async def _query_table(
        self,
        table: str,
        select: str = "*",
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a read-only query against a Supabase table.

        Args:
            table: Table name
            select: Columns to select (PostgREST format)
            filters: Dict of column=value filters (eq only)

        Returns:
            List of row dicts
        """
        if not self.is_connected:
            return []

        params = {"select": select}
        if filters:
            for key, value in filters.items():
                params[key] = f"eq.{value}"

        try:
            response = await self._client.get(f"/{table}", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Supabase HTTP error for site {self.site_id}: {e.response.status_code} - {e.response.text}")
            raise ExternalServiceException("Supabase", f"HTTP {e.response.status_code}")
        except Exception as e:
            logger.error(f"Supabase query error for site {self.site_id}: {e}")
            raise ExternalServiceException("Supabase", str(e))

    async def get_latest_data(self) -> Dict[str, Dict[str, Any]]:
        """Fetch latest sensor data for this site.

        Returns nested dict: {device_id: {datapoint: {value, updated_at}}}
        Returns empty dict if not connected or query fails.
        """
        if not self.is_connected:
            return {}

        try:
            rows = await self._query_table(
                table="latest_data",
                select="device_id,datapoint,value,updated_at",
                filters={"site_id": self.site_id},
            )

            # Transform flat rows to nested structure
            result: Dict[str, Dict[str, Any]] = {}
            for row in rows:
                device_id = row["device_id"]
                datapoint = row["datapoint"]
                if device_id not in result:
                    result[device_id] = {}
                result[device_id][datapoint] = {
                    "value": row["value"],
                    "updated_at": row["updated_at"],
                }

            return result

        except ExternalServiceException:
            raise
        except Exception as e:
            logger.error(f"Supabase query error for site {self.site_id}: {e}")
            raise ExternalServiceException("Supabase", str(e))

    async def get_device_data(self, device_id: str) -> Dict[str, Any]:
        """Fetch latest data for a specific device.

        Returns empty dict if not connected or query fails.
        """
        if not self.is_connected:
            return {}

        try:
            # Use PostgREST query params for multiple filters
            if not self._client:
                return {}

            params = {
                "select": "datapoint,value,updated_at",
                "site_id": f"eq.{self.site_id}",
                "device_id": f"eq.{device_id}",
            }

            response = await self._client.get("/latest_data", params=params)
            response.raise_for_status()
            rows = response.json()

            result = {}
            for row in rows:
                result[row["datapoint"]] = {
                    "value": row["value"],
                    "updated_at": row["updated_at"],
                }

            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Supabase HTTP error for site {self.site_id}: {e.response.status_code}")
            raise ExternalServiceException("Supabase", f"HTTP {e.response.status_code}")
        except Exception as e:
            logger.error(f"Supabase query error for site {self.site_id}: {e}")
            raise ExternalServiceException("Supabase", str(e))



class SupabaseConnectionManager:
    """Manages Supabase connections for multiple sites.

    Creates and caches connections per site based on config/sites.yaml.
    """

    def __init__(self):
        self._connections: Dict[str, SupabaseConnection] = {}

    async def get_connection(self, site_id: str) -> SupabaseConnection:
        """Get or create a Supabase connection for a site."""
        if site_id not in self._connections:
            config = get_site_supabase_config(site_id)

            if config and config.is_configured:
                conn = SupabaseConnection(site_id, config)
                await conn.connect()
            else:
                # Create a mock connection for sites without Supabase config
                logger.info(f"No Supabase config for site {site_id}, using mock mode")
                conn = SupabaseConnection(site_id, SupabaseConfig())

            self._connections[site_id] = conn

        return self._connections[site_id]

    async def close_all(self) -> None:
        """Close all connections."""
        for conn in self._connections.values():
            await conn.close()
        self._connections.clear()
        logger.info("Closed all Supabase connections")


# Global connection manager
_supabase_manager: Optional[SupabaseConnectionManager] = None


async def init_supabase() -> None:
    """Initialize the global Supabase connection manager."""
    global _supabase_manager
    _supabase_manager = SupabaseConnectionManager()
    logger.info("Supabase connection manager initialized")


def get_supabase_manager() -> SupabaseConnectionManager:
    """Get the Supabase connection manager."""
    if _supabase_manager is None:
        raise RuntimeError("Supabase connection manager not initialized")
    return _supabase_manager


async def get_supabase(site_id: str) -> SupabaseConnection:
    """Get a Supabase connection for a specific site."""
    manager = get_supabase_manager()
    return await manager.get_connection(site_id)
