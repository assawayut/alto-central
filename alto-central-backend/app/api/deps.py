"""API dependencies for dependency injection."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.config import settings
from app.core.security import verify_api_key
from app.db.connections.local import LocalDatabase, get_local_db


# Local database dependency (for app data)
def get_local_db_conn() -> LocalDatabase:
    """Get local database connection."""
    return get_local_db()


LocalDBConn = Annotated[LocalDatabase, Depends(get_local_db_conn)]


# Optional API key verification (can be enabled per-route)
async def optional_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> str | None:
    """Optional API key verification."""
    if settings.ENVIRONMENT == "development":
        return None  # Skip in development
    if x_api_key and x_api_key == settings.API_KEY:
        return x_api_key
    return None


OptionalAPIKey = Annotated[str | None, Depends(optional_api_key)]
RequiredAPIKey = Annotated[str, Depends(verify_api_key)]


# Note: Supabase and TimescaleDB connections are now per-site.
# Use `get_supabase(site_id)` and `get_timescale(site_id)` directly in endpoints.
# See app/db/connections/supabase.py and app/db/connections/timescale.py
