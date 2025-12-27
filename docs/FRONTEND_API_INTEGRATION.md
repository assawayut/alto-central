# Frontend API Integration Guide

This document explains how to integrate the Alto Central frontend with the backend API for real-time data.

## Backend API Base URL

```
Development: http://localhost:8642/api/v1
```

## Replacing Mock Data with API Calls

The frontend currently uses mock data in `src/features/`. Replace these with actual API calls.

---

## 1. Real-time Data

### Current Mock Location
`src/features/realtime/index.ts`

### API Endpoint
```
GET /api/v1/sites/{site_id}/realtime/latest
```

### Response Structure
```typescript
interface RealtimeResponse {
  site_id: string;
  timestamp: string;  // ISO 8601
  devices: {
    [device_id: string]: {
      [datapoint: string]: {
        value: number;
        updated_at: string;  // ISO 8601
      };
    };
  };
}
```

### Example Fetch
```typescript
async function fetchRealtimeData(siteId: string): Promise<RealtimeResponse> {
  const response = await fetch(`http://localhost:8642/api/v1/sites/${siteId}/realtime/latest`);
  return response.json();
}
```

### Usage in Components
```typescript
// Replace mock getValue() with:
const data = await fetchRealtimeData(siteId);
const chillerPower = data.devices['chiller_1']?.power?.value ?? 0;
const chillerStatus = data.devices['chiller_1']?.status_read?.value ?? 0;
```

### Key Device IDs
| Device ID | Description |
|-----------|-------------|
| `plant` | Plant-level aggregated values |
| `chiller_1`, `chiller_2`, ... | Individual chillers |
| `pchp_1`, `pchp_2`, ... | Primary chilled water pumps |
| `cdp_1`, `cdp_2`, ... | Condenser water pumps |
| `ct_1`, `ct_2`, ... | Cooling towers |
| `chilled_water_loop` | CHW loop sensors |
| `condenser_water_loop` | CDW loop sensors |
| `outdoor_weather_station` | Weather data |

### Key Datapoints
| Datapoint | Unit | Description |
|-----------|------|-------------|
| `power` | kW | Power consumption |
| `cooling_rate` | RT | Cooling capacity |
| `efficiency` | kW/RT | Energy efficiency |
| `status_read` | 0/1 | Running status |
| `alarm` | 0/1 | Alarm status |
| `supply_water_temperature` | °F | Supply water temp |
| `return_water_temperature` | °F | Return water temp |
| `flow_rate` | GPM | Water flow rate |

---

## 2. Plant Summary (Pre-aggregated)

### API Endpoint
```
GET /api/v1/sites/{site_id}/realtime/plant
```

### Response Structure
```typescript
interface PlantSummary {
  site_id: string;
  plant: {
    power_kw: number;
    cooling_rate_rt: number;
    efficiency_kw_rt: number;
    heat_reject_rt: number;
  };
  chilled_water: {
    supply_temp_f: number;
    return_temp_f: number;
    delta_t: number;
    flow_rate_gpm: number;
  };
  condenser_water: {
    supply_temp_f: number;
    return_temp_f: number;
    delta_t: number;
    flow_rate_gpm: number;
  };
  weather: {
    drybulb_temp_f: number;
    wetbulb_temp_f: number;
    humidity_pct: number;
  };
}
```

### Use Cases
- `PowerCard` component - use `plant.power_kw`, `plant.cooling_rate_rt`
- `EfficiencyCard` component - use `plant.efficiency_kw_rt`
- `WeatherStationCard` component - use `weather.*`
- `PlantDiagram` temperatures - use `chilled_water.*`, `condenser_water.*`

---

## 3. Energy Data

### API Endpoint
```
GET /api/v1/sites/{site_id}/energy/daily
```

### Response Structure
```typescript
interface EnergyDailyResponse {
  site_id: string;
  yesterday: {
    total: number | null;   // kWh
    plant: number | null;   // kWh
    air_side: number | null; // kWh (null for water-only sites)
  };
  today: {
    total: number | null;
    plant: number | null;
    air_side: number | null;
  };
  unit: string;  // "kWh"
}
```

### Use Case
`EnergyUsageCard` component:
```typescript
const energy = await fetch(`/api/v1/sites/${siteId}/energy/daily`).then(r => r.json());

// Display
yesterdayTotal = energy.yesterday.total ?? 'N/A';
todayTotal = energy.today.total ?? 'N/A';
```

---

## 4. Historical Timeseries Data

### API Endpoint (Simple)
```
GET /api/v1/sites/{site_id}/timeseries/aggregated
```

### Query Parameters
| Parameter | Default | Options | Description |
|-----------|---------|---------|-------------|
| `device_id` | `plant` | Any device ID | Device to query |
| `datapoint` | `power` | Any datapoint | Datapoint to query |
| `period` | `24h` | `24h`, `7d`, `30d` | Time range |
| `aggregation` | `hourly` | `hourly`, `daily` | Aggregation level |

### Response Structure
```typescript
interface TimeseriesAggregatedResponse {
  site_id: string;
  device_id: string;
  datapoint: string;
  period: string;
  aggregation: string;
  data: Array<{
    timestamp: string;  // ISO 8601
    value: number;
  }>;
}
```

### Example Fetch
```typescript
async function fetchTimeseries(
  siteId: string,
  deviceId: string = 'plant',
  datapoint: string = 'power',
  period: string = '24h'
): Promise<TimeseriesAggregatedResponse> {
  const params = new URLSearchParams({ device_id: deviceId, datapoint, period });
  const response = await fetch(
    `http://localhost:8642/api/v1/sites/${siteId}/timeseries/aggregated?${params}`
  );
  return response.json();
}
```

### Use Case
`BuildingLoadGraph` component:
```typescript
const data = await fetchTimeseries(siteId, 'plant', 'power', '24h');

// Transform for ECharts
const chartData = data.data.map(d => ({
  time: new Date(d.timestamp),
  value: d.value
}));
```

### API Endpoint (Advanced)
```
POST /api/v1/sites/{site_id}/timeseries/query
```

### Request Body
```typescript
interface TimeseriesQuery {
  device_id: string;
  datapoints: string[];  // Can query multiple datapoints
  start_timestamp: string;  // ISO 8601
  end_timestamp: string;    // ISO 8601
  resampling?: string;      // '1m', '5m', '15m', '30m', '1h', '6h', '1d'
}
```

### Example
```typescript
const response = await fetch(`${API_BASE}/sites/${siteId}/timeseries/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    device_id: 'chiller_1',
    datapoints: ['power', 'cooling_rate', 'efficiency'],
    start_timestamp: '2025-12-26T00:00:00',
    end_timestamp: '2025-12-27T00:00:00',
    resampling: '1h'
  })
});
```

---

## 5. Sites List

### API Endpoint
```
GET /api/v1/sites
```

### Response Structure
```typescript
interface Site {
  site_id: string;
  site_name: string;
  site_code: string;
  latitude: number;
  longitude: number;
  timezone: string;
  has_timescaledb: boolean;
  has_supabase: boolean;
}

type SitesResponse = Site[];
```

### Use Case
Site map page - list all available sites with their database status.

---

## 6. Polling vs WebSocket

### Current Approach: Polling
For now, use polling with `setInterval`:

```typescript
useEffect(() => {
  const fetchData = async () => {
    const data = await fetchRealtimeData(siteId);
    setDevices(data.devices);
  };

  fetchData();  // Initial fetch
  const interval = setInterval(fetchData, 10000);  // Poll every 10 seconds

  return () => clearInterval(interval);
}, [siteId]);
```

### Future: WebSocket
WebSocket endpoint will be added for true real-time updates:
```
ws://localhost:8642/ws/sites/{site_id}/realtime
```

---

## 7. Error Handling

### Empty Response
When no data is available, the API returns empty objects:
```json
{
  "site_id": "mbk",
  "timestamp": "2025-12-27T13:20:00",
  "devices": {}
}
```

### Null Values
Energy data may contain `null` for unavailable metrics:
```json
{
  "yesterday": {"total": null, "plant": null, "air_side": null}
}
```

Handle in UI:
```typescript
const displayValue = value !== null ? value.toFixed(2) : 'N/A';
```

---

## 8. CORS Configuration

The backend allows CORS from all origins in development. For production, configure allowed origins in backend settings.

---

## 9. Example: Replacing useRealtime Hook

### Before (Mock)
```typescript
// src/features/realtime/index.ts
export function useRealtime() {
  const getValue = (deviceId: string, datapoint: string) => {
    return mockData[deviceId]?.[datapoint] ?? 0;
  };
  return { getValue };
}
```

### After (API)
```typescript
// src/features/realtime/index.ts
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

const API_BASE = 'http://localhost:8642/api/v1';

export function useRealtime() {
  const { siteId } = useParams<{ siteId: string }>();
  const [devices, setDevices] = useState<Record<string, any>>({});

  useEffect(() => {
    if (!siteId) return;

    const fetchData = async () => {
      try {
        const res = await fetch(`${API_BASE}/sites/${siteId}/realtime/latest`);
        const data = await res.json();
        setDevices(data.devices || {});
      } catch (err) {
        console.error('Failed to fetch realtime data:', err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [siteId]);

  const getValue = (deviceId: string, datapoint: string): number => {
    return devices[deviceId]?.[datapoint]?.value ?? 0;
  };

  const getUpdatedAt = (deviceId: string, datapoint: string): string | null => {
    return devices[deviceId]?.[datapoint]?.updated_at ?? null;
  };

  return { getValue, getUpdatedAt, devices };
}
```

---

## 10. Animation Triggers

The `PlantDiagram` animation depends on flow rate values:

```typescript
// Check if water is flowing
const chwFlowing = devices['chilled_water_loop']?.flow_rate?.value >= 1;
const cdwFlowing = devices['condenser_water_loop']?.flow_rate?.value >= 1;
```

---

## 11. Testing API Endpoints

Use curl to test endpoints:

```bash
# List sites
curl http://localhost:8642/api/v1/sites

# Get real-time data
curl http://localhost:8642/api/v1/sites/kspo/realtime/latest

# Get plant summary
curl http://localhost:8642/api/v1/sites/kspo/realtime/plant

# Get energy data
curl http://localhost:8642/api/v1/sites/kspo/energy/daily

# Get historical timeseries (hourly plant power, last 24h)
curl "http://localhost:8642/api/v1/sites/kspo/timeseries/aggregated?device_id=plant&datapoint=power&period=24h"

# Get historical timeseries (daily, last 30 days)
curl "http://localhost:8642/api/v1/sites/kspo/timeseries/aggregated?device_id=plant&datapoint=power&period=30d&aggregation=daily"
```

Or use the Swagger UI at: http://localhost:8642/docs
