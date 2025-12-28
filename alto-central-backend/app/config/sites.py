"""Load site configuration from shared YAML file.

This module loads the sites.yaml configuration that is shared between
the frontend and backend. Each site can have its own database configuration.

Structure:
  sites:
    - site_id: kspo
      database:
        timescaledb:
          host: 10.144.168.147
          port: 5433
          ...
        supabase:
          url: https://...
          anon_key: ...
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class TimescaleConfig(BaseModel):
    """TimescaleDB connection configuration for a site."""

    host: str = ""
    port: int = 5432
    database: str = "postgres"
    user: str = "postgres"
    password: str = ""
    ssl_mode: str = "disable"  # disable for internal IPs, require for external

    @property
    def is_configured(self) -> bool:
        """Check if TimescaleDB is properly configured."""
        return bool(self.host and self.database and self.user)


class SupabaseConfig(BaseModel):
    """Supabase connection configuration for a site."""

    url: str = ""
    anon_key: str = ""
    service_key: str = ""

    @property
    def is_configured(self) -> bool:
        """Check if Supabase is properly configured."""
        return bool(self.url and (self.anon_key or self.service_key))

    @property
    def api_key(self) -> str:
        """Get the API key to use (prefer service key if available)."""
        return self.service_key or self.anon_key


class MongoDBConfig(BaseModel):
    """MongoDB connection configuration for a site."""

    uri: str = ""

    @property
    def is_configured(self) -> bool:
        """Check if MongoDB is properly configured."""
        return bool(self.uri)

    @property
    def clean_uri(self) -> str:
        """Get cleaned URI (remove double slashes at end)."""
        uri = self.uri.rstrip("/")
        return uri


class SiteDatabaseConfig(BaseModel):
    """Database configuration for a site."""

    timescaledb: Optional[TimescaleConfig] = None
    supabase: Optional[SupabaseConfig] = None
    mongodb: Optional[MongoDBConfig] = None


class MapConfig(BaseModel):
    """Map display configuration."""

    center: Dict[str, float] = Field(
        default_factory=lambda: {"latitude": 13.7563, "longitude": 100.5018}
    )
    zoom: int = 6


class SiteConfig(BaseModel):
    """Individual site configuration."""

    site_id: str
    site_name: str
    site_code: str = ""
    latitude: float
    longitude: float
    timezone: str = "UTC"
    hvac_type: str = "water"  # "water" = water-side only, "air" = includes air-side
    building_type: str = "office"  # office, retail, hotel, etc.
    database: Optional[SiteDatabaseConfig] = None

    def get_timescale_config(self) -> Optional[TimescaleConfig]:
        """Get TimescaleDB config for this site."""
        if self.database and self.database.timescaledb:
            return self.database.timescaledb
        return None

    def get_supabase_config(self) -> Optional[SupabaseConfig]:
        """Get Supabase config for this site."""
        if self.database and self.database.supabase:
            return self.database.supabase
        return None

    def get_mongodb_config(self) -> Optional[MongoDBConfig]:
        """Get MongoDB config for this site."""
        if self.database and self.database.mongodb:
            return self.database.mongodb
        return None

    @property
    def has_timescaledb(self) -> bool:
        """Check if site has TimescaleDB configured."""
        config = self.get_timescale_config()
        return config is not None and config.is_configured

    @property
    def has_supabase(self) -> bool:
        """Check if site has Supabase configured."""
        config = self.get_supabase_config()
        return config is not None and config.is_configured

    @property
    def has_mongodb(self) -> bool:
        """Check if site has MongoDB configured."""
        config = self.get_mongodb_config()
        return config is not None and config.is_configured


class SitesConfig(BaseModel):
    """Root configuration from sites.yaml."""

    map: MapConfig = Field(default_factory=MapConfig)
    sites: List[SiteConfig] = Field(default_factory=list)


def find_config_file() -> Path:
    """Find the sites.yaml configuration file.

    Searches in order:
    1. ALTO_CONFIG_PATH environment variable
    2. ../config/sites.yaml (relative to backend)
    3. ../../config/sites.yaml (from app directory)
    """
    # Check environment variable
    env_path = os.environ.get("ALTO_CONFIG_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path

    # Check relative paths
    base_paths = [
        Path(__file__).parent.parent.parent.parent / "config" / "sites.yaml",  # from app/config/
        Path.cwd().parent / "config" / "sites.yaml",  # from alto-central-backend/
        Path.cwd() / "config" / "sites.yaml",  # from alto-central/
    ]

    for path in base_paths:
        if path.exists():
            return path.resolve()

    raise FileNotFoundError(
        "Could not find sites.yaml. Set ALTO_CONFIG_PATH environment variable "
        "or ensure config/sites.yaml exists in the project root."
    )


@lru_cache
def load_sites_config() -> SitesConfig:
    """Load and parse the sites configuration.

    Returns cached config on subsequent calls.
    """
    config_path = find_config_file()

    with open(config_path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    return SitesConfig(**raw_config)


def get_sites() -> List[SiteConfig]:
    """Get list of all configured sites."""
    config = load_sites_config()
    return config.sites


def get_site_by_id(site_id: str) -> Optional[SiteConfig]:
    """Get a specific site by its ID."""
    config = load_sites_config()
    for site in config.sites:
        if site.site_id == site_id:
            return site
    return None


def get_site_timescale_config(site_id: str) -> Optional[TimescaleConfig]:
    """Get TimescaleDB configuration for a specific site."""
    site = get_site_by_id(site_id)
    if site:
        return site.get_timescale_config()
    return None


def get_site_supabase_config(site_id: str) -> Optional[SupabaseConfig]:
    """Get Supabase configuration for a specific site."""
    site = get_site_by_id(site_id)
    if site:
        return site.get_supabase_config()
    return None


def get_site_mongodb_config(site_id: str) -> Optional[MongoDBConfig]:
    """Get MongoDB configuration for a specific site."""
    site = get_site_by_id(site_id)
    if site:
        return site.get_mongodb_config()
    return None


def reload_config() -> SitesConfig:
    """Force reload the configuration (clears cache)."""
    load_sites_config.cache_clear()
    return load_sites_config()
