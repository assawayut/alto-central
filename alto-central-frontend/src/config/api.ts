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

  // Analytics
  plantPerformance: (siteId: string, params: {
    start_date?: string;
    end_date?: string;
    resolution?: string;
    start_time?: string;
    end_time?: string;
    day_type?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params.start_date) searchParams.set('start_date', params.start_date);
    if (params.end_date) searchParams.set('end_date', params.end_date);
    if (params.resolution) searchParams.set('resolution', params.resolution);
    if (params.start_time) searchParams.set('start_time', params.start_time);
    if (params.end_time) searchParams.set('end_time', params.end_time);
    if (params.day_type) searchParams.set('day_type', params.day_type);
    return `${API_BASE_URL}/sites/${siteId}/analytics/plant-performance?${searchParams}`;
  },

  coolingTowerTradeoff: (siteId: string, params: {
    start_date?: string;
    end_date?: string;
    resolution?: string;
    start_time?: string;
    end_time?: string;
    day_type?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params.start_date) searchParams.set('start_date', params.start_date);
    if (params.end_date) searchParams.set('end_date', params.end_date);
    if (params.resolution) searchParams.set('resolution', params.resolution);
    if (params.start_time) searchParams.set('start_time', params.start_time);
    if (params.end_time) searchParams.set('end_time', params.end_time);
    if (params.day_type) searchParams.set('day_type', params.day_type);
    return `${API_BASE_URL}/sites/${siteId}/analytics/cooling-tower-tradeoff?${searchParams}`;
  },

  // Events
  events: (siteId: string, params?: { status?: string; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    const query = searchParams.toString();
    return `${API_BASE_URL}/sites/${siteId}/events/${query ? `?${query}` : ''}`;
  },

  eventsUpcoming: (siteId: string, params?: { hours_ahead?: number; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.hours_ahead) searchParams.set('hours_ahead', params.hours_ahead.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    const query = searchParams.toString();
    return `${API_BASE_URL}/sites/${siteId}/events/upcoming${query ? `?${query}` : ''}`;
  },
};

// Polling interval in milliseconds
export const POLLING_INTERVAL = 10000; // 10 seconds
