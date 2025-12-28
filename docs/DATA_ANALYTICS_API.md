# Data Analytics API Requirements

This document defines the API endpoint needed for the Data Analytics feature in the frontend.

> **Scope**: This API is for **water-side (chiller plant) analytics only**.
> Air-side analytics (AHUs, fans) will use a separate endpoint (`/analytics/airside-performance`) when needed.

---

## Plant Performance Scatter Plot API (Water-Side)

### Endpoint
```
GET /api/v1/sites/{site_id}/analytics/plant-performance
```

### Purpose
Provides scatter plot data for analyzing **chiller plant** efficiency or power vs cooling load, with filtering and grouping by chiller combinations. This endpoint returns water-side data regardless of the site's `hvac_type` configuration, since all sites have a chiller plant.

---

### Query Parameters

| Parameter | Required | Default | Options | Description |
|-----------|----------|---------|---------|-------------|
| `start_date` | No | 3 months ago | `YYYY-MM-DD` | Start of date range |
| `end_date` | No | today | `YYYY-MM-DD` | End of date range |
| `resolution` | No | `1h` | `1m`, `15m`, `1h` | Time resolution for data aggregation |
| `start_time` | No | `00:00` | `HH:MM` | Filter by time of day (start) |
| `end_time` | No | `23:59` | `HH:MM` | Filter by time of day (end) |
| `day_type` | No | `all` | `all`, `weekdays`, `weekends` | Filter by day type |

---

### Response Structure

```typescript
interface PlantPerformanceResponse {
  site_id: string;
  start_date: string;
  end_date: string;
  resolution: string;
  filters: {
    start_time: string;
    end_time: string;
    day_type: string;
  };
  data: Array<{
    timestamp: string;           // ISO 8601 with timezone
    cooling_load: number;        // RT
    power: number;               // kW
    efficiency: number;          // kW/RT (calculated: power / cooling_load)
    num_chillers: number;        // 1, 2, 3, 4, 5...
    chiller_combination: string; // "CH-1", "CH-1+CH-2", "CH-1+CH-2+CH-3", etc.
    // Additional fields for secondary labeling
    chs: number;                 // Chilled water supply temp (°F)
    cds: number;                 // Condenser water supply temp (°F)
    outdoor_wbt: number;         // Outdoor wet-bulb temp (°F)
    outdoor_dbt: number;         // Outdoor dry-bulb temp (°F)
  }>;
}
```

### Data Source Mapping

| Response Field | Device ID | Datapoint |
|----------------|-----------|-----------|
| `cooling_load` | `plant` | `cooling_rate` |
| `power` | `plant` | `power` |
| `chs` | `chilled_water_loop` | `supply_water_temperature` |
| `cds` | `condenser_water_loop` | `supply_water_temperature` |
| `outdoor_wbt` | `outdoor_weather_station` | `wetbulb_temperature` |
| `outdoor_dbt` | `outdoor_weather_station` | `drybulb_temperature` |
| `num_chillers` | `chiller_1`, `chiller_2`, ... | `status_read` (count where = 1) |
| `chiller_combination` | `chiller_1`, `chiller_2`, ... | `status_read` (join IDs where = 1) |

> **Note:** Data already exists in 1m, 15m, and 1h tables - no resampling needed. Just query from the appropriate table based on `resolution` parameter.

### Secondary Labeling

The frontend supports two-level labeling using **color** and **shape**:

| Visual | Label By |
|--------|----------|
| Color | Primary: any field (e.g., `num_chillers`, `chiller_combination`, temps) |
| Shape | Secondary: any field (binned into ranges for continuous values) |

**Binning Strategy** (frontend handles this, user-configurable):
- CHS: 2°F bins (e.g., 42-44, 44-46, 46-48°F)
- CDS: 3°F bins (e.g., 82-85, 85-88, 88-91°F)
- Outdoor WBT: 3°F bins (e.g., 65-68, 68-71, 71-74°F)
- Outdoor DBT: 5°F bins (e.g., 75-80, 80-85, 85-90°F)

---

### Example Request

```bash
# Get 3 months of data at 15-min resolution, weekdays only, 9AM-6PM
curl "http://localhost:8642/api/v1/sites/kspo/analytics/plant-performance?start_date=2025-09-28&end_date=2025-12-28&resolution=15m&start_time=09:00&end_time=18:00&day_type=weekdays"
```

---

### Example Response

```json
{
  "site_id": "kspo",
  "start_date": "2025-09-28",
  "end_date": "2025-12-28",
  "resolution": "15m",
  "filters": {
    "start_time": "09:00",
    "end_time": "18:00",
    "day_type": "weekdays"
  },
  "data": [
    {
      "timestamp": "2025-10-15T14:00:00+07:00",
      "cooling_load": 150.5,
      "power": 120.3,
      "efficiency": 0.80,
      "num_chillers": 2,
      "chiller_combination": "CH-1+CH-2",
      "chs": 44.2,
      "cds": 85.1,
      "outdoor_wbt": 68.5,
      "outdoor_dbt": 82.3
    },
    {
      "timestamp": "2025-10-15T14:15:00+07:00",
      "cooling_load": 180.2,
      "power": 138.5,
      "efficiency": 0.77,
      "num_chillers": 2,
      "chiller_combination": "CH-1+CH-3",
      "chs": 44.5,
      "cds": 86.2,
      "outdoor_wbt": 69.1,
      "outdoor_dbt": 83.0
    },
    {
      "timestamp": "2025-10-16T10:00:00+07:00",
      "cooling_load": 95.0,
      "power": 85.5,
      "efficiency": 0.90,
      "num_chillers": 1,
      "chiller_combination": "CH-1",
      "chs": 43.8,
      "cds": 82.5,
      "outdoor_wbt": 65.2,
      "outdoor_dbt": 78.5
    }
  ]
}
```

---

## Frontend Use Cases

The frontend will use this single API to support multiple analysis scenarios:

### 1. Overall Plant Performance Curve
```
Request: GET /analytics/plant-performance?start_date=2025-09-28&end_date=2025-12-28&resolution=1h
Frontend: Plot all points, color by num_chillers (1, 2, 3, 4, 5)
```

### 2. Compare Individual Chillers
```
Request: GET /analytics/plant-performance?start_date=2025-09-28&end_date=2025-12-28&resolution=15m
Frontend Filter: num_chillers = 1
Frontend Color: chiller_combination (shows CH-1, CH-2, CH-3 as separate colors)
```

### 3. Compare 2-Chiller Combinations
```
Request: GET /analytics/plant-performance?start_date=2025-09-28&end_date=2025-12-28&resolution=15m
Frontend Filter: num_chillers = 2
Frontend Color: chiller_combination (shows CH-1+CH-2, CH-1+CH-3, CH-2+CH-3)
```

### 4. Peak Hours Analysis
```
Request: GET /analytics/plant-performance?start_date=2025-09-28&end_date=2025-12-28&resolution=1m&start_time=13:00&end_time=16:00&day_type=weekdays
Frontend: Analyze only peak afternoon data on working days with 1-minute granularity
```

---

## Backend Implementation Notes

### 1. Data Source
Query from the appropriate resolution table (1m/15m/1h) based on `resolution` parameter:

| Field | Device ID | Datapoint |
|-------|-----------|-----------|
| power | `plant` | `power` |
| cooling_load | `plant` | `cooling_rate` |
| chs | `chilled_water_loop` | `supply_water_temperature` |
| cds | `condenser_water_loop` | `supply_water_temperature` |
| outdoor_wbt | `outdoor_weather_station` | `wetbulb_temperature` |
| outdoor_dbt | `outdoor_weather_station` | `drybulb_temperature` |
| chiller status | `chiller_1`, `chiller_2`, ... | `status_read` (0/1) |

### 2. Determining `num_chillers`
At each timestamp, count chillers where `status_read = 1`:
```python
num_chillers = sum(1 for ch in chillers if ch.status_read == 1)
```

### 3. Determining `chiller_combination`
Sort running chiller IDs alphabetically and join with "+":
```python
running = sorted([ch.id for ch in chillers if ch.status_read == 1])
chiller_combination = "+".join(running)  # e.g., "CH-1+CH-3"
```

### 4. Efficiency Calculation
```python
efficiency = power / cooling_load if cooling_load > 0 else None
```
- Skip data points where `cooling_load < 10 RT` (avoid noise at very low loads)

### 5. Resolution Tables
Data already exists in separate tables - just query from the correct one:
- `resolution=1m`: Query from 1-minute table
- `resolution=15m`: Query from 15-minute table
- `resolution=1h`: Query from 1-hour table

Approximate data point counts for 1 month:
- `1m`: ~43,200 points
- `15m`: ~2,880 points
- `1h`: ~720 points

### 6. Timezone
- All timestamps must be in site's local timezone (from `config/sites.yaml`)
- Filter `start_time`/`end_time` should apply to local time

### 7. Performance
- Consider caching results for common queries
- For 3+ month queries, response may have 2000+ data points - this is acceptable for scatter plots

---

## Frontend Filters (Applied Client-Side)

The frontend will apply additional filters on the response data:

| Filter | UI Element | Purpose |
|--------|------------|---------|
| Y-Axis Toggle | Dropdown | Switch between Efficiency and Power |
| Num Chillers | Checkboxes | Filter to show only 1, 2, 3... chillers |
| Label By | Dropdown | Color points by num_chillers OR chiller_combination |

---

## Testing

```bash
# Basic request - default 3 months, hourly resolution
curl "http://localhost:8642/api/v1/sites/kspo/analytics/plant-performance"

# Custom date range, 15-min resolution, weekdays, business hours
curl "http://localhost:8642/api/v1/sites/kspo/analytics/plant-performance?start_date=2025-10-01&end_date=2025-12-28&resolution=15m&start_time=08:00&end_time=18:00&day_type=weekdays"

# 1-minute resolution for detailed analysis (last month)
curl "http://localhost:8642/api/v1/sites/kspo/analytics/plant-performance?start_date=2025-11-28&end_date=2025-12-28&resolution=1m"
```
