"""Sites API endpoints.

Lists all configured sites from the shared sites.yaml configuration.
"""

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_sites, get_site_by_id, SiteConfig

router = APIRouter()


class SiteResponse(BaseModel):
    """Site response without sensitive database info."""

    site_id: str
    site_name: str
    site_code: str = ""
    latitude: float
    longitude: float
    timezone: str = "UTC"
    has_timescaledb: bool = False
    has_supabase: bool = False

    @classmethod
    def from_config(cls, config: SiteConfig) -> "SiteResponse":
        """Create response from config, excluding database credentials."""
        return cls(
            site_id=config.site_id,
            site_name=config.site_name,
            site_code=config.site_code,
            latitude=config.latitude,
            longitude=config.longitude,
            timezone=config.timezone,
            has_timescaledb=config.has_timescaledb,
            has_supabase=config.has_supabase,
        )


@router.get(
    "",
    response_model=List[SiteResponse],
    summary="List all sites",
    description="Get all sites configured in the system.",
)
async def list_sites() -> List[SiteResponse]:
    """List all configured sites."""
    return [SiteResponse.from_config(s) for s in get_sites()]


@router.get(
    "/{site_id}",
    response_model=SiteResponse,
    summary="Get site details",
    description="Get details for a specific site.",
)
async def get_site(site_id: str) -> SiteResponse:
    """Get a specific site by ID."""
    site = get_site_by_id(site_id)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found")
    return SiteResponse.from_config(site)
