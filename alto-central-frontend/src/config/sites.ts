/**
 * Site Configuration
 *
 * This file loads site configuration from the shared YAML file.
 * The YAML file is located at: alto-central/config/sites.yaml
 *
 * To add a new site, edit the YAML file - both frontend and backend will use it.
 */

import sitesConfig from '@config/sites.yaml';

export interface SiteConfig {
  // Required fields
  site_id: string;
  site_name: string;
  site_code: string;  // Short code for map display (e.g., "NKW", "AYY")
  latitude: number;
  longitude: number;

  // Optional fields
  ip?: string;
  timezone?: string;
  hvac_type?: string;  // e.g., water, air, both, water_air_integration, hotel, wholesale
  building_type?: string;
  design_capacity_rt?: number;  // Design cooling capacity in RT for part-load calculation

  // Database config (for backend use)
  database?: {
    timescaledb_host?: string;
    timescaledb_port?: number;
    supabase_url?: string;
    supabase_anon_key?: string;
  };
}

export interface MapConfig {
  center: {
    latitude: number;
    longitude: number;
  };
  zoom: number;
}

// Load sites from YAML
export const sites: SiteConfig[] = sitesConfig.sites || [];

// Load map config from YAML
export const mapConfig: MapConfig = sitesConfig.map || {
  center: { latitude: 13.7563, longitude: 100.5018 },
  zoom: 6,
};

// For backwards compatibility
export const defaultMapCenter = {
  latitude: mapConfig.center.latitude,
  longitude: mapConfig.center.longitude,
  zoom: mapConfig.zoom,
};

/**
 * Get a site by its ID
 */
export function getSiteById(siteId: string): SiteConfig | undefined {
  return sites.find(site => site.site_id === siteId);
}

/**
 * Get all sites
 */
export function getAllSites(): SiteConfig[] {
  return sites;
}
