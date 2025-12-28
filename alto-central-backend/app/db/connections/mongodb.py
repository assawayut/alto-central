"""MongoDB connection management for per-site connections.

Uses motor (async MongoDB driver) for async support.
Each site can have its own MongoDB instance configured in sites.yaml.
"""

import logging
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_site_mongodb_config

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """Async MongoDB connection for a specific site."""

    def __init__(self, site_id: str):
        self.site_id = site_id
        self._client: Optional[AsyncIOMotorClient] = None
        self._db_control: Optional[AsyncIOMotorDatabase] = None
        self._is_connected = False

    async def connect(self) -> bool:
        """Connect to MongoDB for this site."""
        if self._is_connected:
            return True

        config = get_site_mongodb_config(self.site_id)
        if not config or not config.is_configured:
            logger.debug(f"No MongoDB config for site {self.site_id}")
            return False

        try:
            uri = config.clean_uri
            self._client = AsyncIOMotorClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            # Test connection
            await self._client.admin.command("ping")

            # Get the control database (where action_event collection lives)
            self._db_control = self._client["control"]

            self._is_connected = True
            logger.info(f"Connected to MongoDB for site {self.site_id}")
            return True

        except Exception as e:
            logger.warning(f"Failed to connect to MongoDB for site {self.site_id}: {e}")
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        """Close the MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db_control = None
            self._is_connected = False
            logger.info(f"Disconnected from MongoDB for site {self.site_id}")

    @property
    def is_connected(self) -> bool:
        """Check if connected to MongoDB."""
        return self._is_connected

    @property
    def control_db(self) -> Optional[AsyncIOMotorDatabase]:
        """Get the control database."""
        return self._db_control

    async def get_action_events(
        self,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Fetch action events from MongoDB.

        Args:
            status: Filter by status (pending, in-progress, completed)
            limit: Maximum number of events to return

        Returns:
            List of action event documents
        """
        # Only check _is_connected flag to avoid pymongo __bool__ issue
        # _db_control is guaranteed to be set when _is_connected is True
        if not self._is_connected:
            return []

        try:
            collection = self._db_control["action_event"]

            # Build query - each site has its own MongoDB, so no site filter needed
            query: Dict[str, Any] = {}
            if status and status != "all":
                query["status"] = status

            # Sort by scheduled_time ascending (upcoming first)
            cursor = collection.find(query).sort("scheduled_time", 1).limit(limit)

            events = []
            async for doc in cursor:
                # Convert ObjectId to string if present
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                events.append(doc)

            return events

        except Exception as e:
            logger.error(f"Error fetching action events for site {self.site_id}: {e}")
            return []


class MongoDBConnectionManager:
    """Manages MongoDB connections for all sites."""

    def __init__(self):
        self._connections: Dict[str, MongoDBConnection] = {}

    async def get_connection(self, site_id: str) -> MongoDBConnection:
        """Get or create a MongoDB connection for a site."""
        if site_id not in self._connections:
            self._connections[site_id] = MongoDBConnection(site_id)

        conn = self._connections[site_id]
        if not conn.is_connected:
            await conn.connect()

        return conn

    async def close_all(self) -> None:
        """Close all MongoDB connections."""
        for conn in self._connections.values():
            await conn.disconnect()
        self._connections.clear()
        logger.info("All MongoDB connections closed")


# Global connection manager
_manager: Optional[MongoDBConnectionManager] = None


def get_mongodb_manager() -> MongoDBConnectionManager:
    """Get the global MongoDB connection manager."""
    global _manager
    if _manager is None:
        _manager = MongoDBConnectionManager()
    return _manager


async def get_mongodb(site_id: str) -> MongoDBConnection:
    """Get a MongoDB connection for a specific site."""
    manager = get_mongodb_manager()
    return await manager.get_connection(site_id)


async def init_mongodb() -> None:
    """Initialize the MongoDB connection manager."""
    global _manager
    _manager = MongoDBConnectionManager()
    logger.info("MongoDB connection manager initialized")


async def close_mongodb() -> None:
    """Close all MongoDB connections."""
    global _manager
    if _manager is not None:
        await _manager.close_all()
        _manager = None
