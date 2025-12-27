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

  // Timeseries
  timeseriesAggregated: (siteId: string, params: {
    device_id?: string;
    datapoint?: string;
    period?: string;
    aggregation?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params.device_id) searchParams.set('device_id', params.device_id);
    if (params.datapoint) searchParams.set('datapoint', params.datapoint);
    if (params.period) searchParams.set('period', params.period);
    if (params.aggregation) searchParams.set('aggregation', params.aggregation);
    return `${API_BASE_URL}/sites/${siteId}/timeseries/aggregated?${searchParams}`;
  },
};

// Polling interval in milliseconds
export const POLLING_INTERVAL = 10000; // 10 seconds
