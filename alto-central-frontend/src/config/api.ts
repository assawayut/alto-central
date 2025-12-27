/**
 * API Configuration
 *
 * Base URL and endpoints for the Alto Central backend API.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8642/api/v1';

export const API_ENDPOINTS = {
  // Sites
  sites: () => `${API_BASE_URL}/sites`,

  // Real-time data
  realtimeLatest: (siteId: string) => `${API_BASE_URL}/sites/${siteId}/realtime/latest`,
  realtimePlant: (siteId: string) => `${API_BASE_URL}/sites/${siteId}/realtime/plant`,

  // Energy
  energyDaily: (siteId: string) => `${API_BASE_URL}/sites/${siteId}/energy/daily`,
};

// Polling interval in milliseconds
export const POLLING_INTERVAL = 10000; // 10 seconds
