"""Database connection management.

Per-site connection managers for:
- Supabase (real-time data)
- TimescaleDB (historical data)
- MongoDB (action events)
- Local PostgreSQL (app data)
"""

from app.db.connections.supabase import (
    SupabaseConnection,
    SupabaseConnectionManager,
    get_supabase,
    get_supabase_manager,
    init_supabase,
)
from app.db.connections.timescale import (
    TimescaleConnection,
    TimescaleConnectionManager,
    get_timescale,
    get_timescale_manager,
    init_timescale,
    close_timescale,
)
from app.db.connections.mongodb import (
    MongoDBConnection,
    MongoDBConnectionManager,
    get_mongodb,
    get_mongodb_manager,
    init_mongodb,
    close_mongodb,
)
from app.db.connections.local import (
    LocalDatabase,
    get_local_db,
    init_local_db,
    close_local_db,
)

__all__ = [
    # Supabase (per-site)
    "SupabaseConnection",
    "SupabaseConnectionManager",
    "get_supabase",
    "get_supabase_manager",
    "init_supabase",
    # TimescaleDB (per-site)
    "TimescaleConnection",
    "TimescaleConnectionManager",
    "get_timescale",
    "get_timescale_manager",
    "init_timescale",
    "close_timescale",
    # MongoDB (per-site)
    "MongoDBConnection",
    "MongoDBConnectionManager",
    "get_mongodb",
    "get_mongodb_manager",
    "init_mongodb",
    "close_mongodb",
    # Local DB
    "LocalDatabase",
    "get_local_db",
    "init_local_db",
    "close_local_db",
]
