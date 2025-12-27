# Backend API Requirements for Alto Central

This document outlines the data requirements for the Alto Central frontend dashboard. The backend needs to provide real-time data and historical timeseries data for HVAC monitoring.

---

## Data Sources

| Priority | Source | Use Case |
|----------|--------|----------|
| Primary | Supabase `latest_data` table | Real-time datapoint values with WebSocket subscription |
| Fallback | TimescaleDB | For sites without Supabase; query latest timestamp |

---

## 1. Real-Time Data API

### Option A: Supabase `latest_data` Table (Preferred)

**Table Schema:**
```sql
CREATE TABLE latest_data (
  device_id TEXT NOT NULL,
  datapoint TEXT NOT NULL,
  value NUMERIC,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  is_stale BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (device_id, datapoint)
);
```

**Expected Response Format (REST or WebSocket):**
```json
{
  "plant": {
    "power": { "value": 186, "updated_at": "2024-01-15T10:30:45Z" },
    "cooling_rate": { "value": 250, "updated_at": "2024-01-15T10:30:45Z" }
  },
  "chiller_1": {
    "status_read": { "value": 1, "updated_at": "2024-01-15T10:30:40Z" },
    "power": { "value": 95, "updated_at": "2024-01-15T10:30:40Z" }
  }
}
```

### Option B: TimescaleDB Latest Query (Fallback)

For sites without Supabase, query the latest value for each datapoint:

```sql
SELECT DISTINCT ON (device_id, datapoint)
  device_id, datapoint, value, timestamp
FROM timeseries_data
WHERE site_id = :site_id
ORDER BY device_id, datapoint, timestamp DESC;
```

---

## 2. Required Datapoints by Device

### 2.1 Plant-Level Aggregates

| device_id | datapoint | unit | description |
|-----------|-----------|------|-------------|
| `plant` | `power` | kW | Total plant power consumption |
| `plant` | `cooling_rate` | RT | Total cooling load (refrigeration tons) |
| `plant` | `efficiency` | kW/RT | Calculated: power / cooling_rate |
| `plant` | `heat_reject` | RT | Heat rejection rate |

### 2.2 Chilled Water Loop

| device_id | datapoint | unit | description |
|-----------|-----------|------|-------------|
| `chilled_water_loop` | `supply_water_temperature` | °F | CHS - Chilled water supply temp |
| `chilled_water_loop` | `return_water_temperature` | °F | CHR - Chilled water return temp |
| `chilled_water_loop` | `flow_rate` | GPM | Chilled water flow rate |

### 2.3 Condenser Water Loop

| device_id | datapoint | unit | description |
|-----------|-----------|------|-------------|
| `condenser_water_loop` | `supply_water_temperature` | °F | CDS - Condenser water supply temp |
| `condenser_water_loop` | `return_water_temperature` | °F | CDR - Condenser water return temp |
| `condenser_water_loop` | `flow_rate` | GPM | Condenser water flow rate |

### 2.4 Chillers (chiller_1, chiller_2, ...)

| device_id | datapoint | unit | description |
|-----------|-----------|------|-------------|
| `chiller_N` | `status_read` | 0/1 | 0=standby, 1=running |
| `chiller_N` | `alarm` | 0/1 | 0=normal, 1=alarm |
| `chiller_N` | `power` | kW | Individual chiller power |
| `chiller_N` | `efficiency` | kW/RT | Individual chiller efficiency |
| `chiller_N` | `setpoint_read` | °F | Chiller setpoint temperature |
| `chiller_N` | `evap_leaving_water_temperature` | °F | CHS from chiller |
| `chiller_N` | `evap_entering_water_temperature` | °F | CHR from chiller |
| `chiller_N` | `cond_entering_water_temperature` | °F | CDR from chiller |
| `chiller_N` | `cond_leaving_water_temperature` | °F | CDS from chiller |

### 2.5 Primary Chilled Water Pumps (pchp_1, pchp_2, ...)

| device_id | datapoint | unit | description |
|-----------|-----------|------|-------------|
| `pchp_N` | `status_read` | 0/1 | 0=standby, 1=running |
| `pchp_N` | `alarm` | 0/1 | 0=normal, 1=alarm |
| `pchp_N` | `power` | kW | Pump power consumption |
| `pchp_N` | `frequency_read` | Hz | VFD frequency (if applicable) |

### 2.6 Condenser Water Pumps (cdp_1, cdp_2, ...)

| device_id | datapoint | unit | description |
|-----------|-----------|------|-------------|
| `cdp_N` | `status_read` | 0/1 | 0=standby, 1=running |
| `cdp_N` | `alarm` | 0/1 | 0=normal, 1=alarm |
| `cdp_N` | `power` | kW | Pump power consumption |
| `cdp_N` | `frequency_read` | Hz | VFD frequency (if applicable) |

### 2.7 Cooling Towers (cooling_tower_1, cooling_tower_2, ...)

| device_id | datapoint | unit | description |
|-----------|-----------|------|-------------|
| `cooling_tower_N` | `status_read` | 0/1 | 0=standby, 1=running |
| `cooling_tower_N` | `alarm` | 0/1 | 0=normal, 1=alarm |
| `cooling_tower_N` | `power` | kW | Fan motor power |
| `cooling_tower_N` | `frequency_read` | Hz | Fan speed frequency |

### 2.8 Weather Station

| device_id | datapoint | unit | description |
|-----------|-----------|------|-------------|
| `outdoor_weather_station` | `drybulb_temperature` | °F | Outdoor dry bulb temp (DBT) |
| `outdoor_weather_station` | `wetbulb_temperature` | °F | Outdoor wet bulb temp (WBT) |
| `outdoor_weather_station` | `humidity` | % | Relative humidity |

---

## 3. Ontology / Equipment List API

Frontend needs to know what equipment exists at each site.

### Endpoint
```
GET /api/sites/{site_id}/ontology/entities
```

### Query Parameters
- `tag_filter`: Filter by tag (e.g., `spaceRef:plant`, `model:chiller`)
- `expand`: Include additional data (`tags`, `latest_data`)

### Response Format
```json
{
  "entities": [
    {
      "entity_id": "chiller_1",
      "name": "Chiller 1",
      "tags": {
        "model": "chiller",
        "spaceRef": "plant"
      }
    },
    {
      "entity_id": "pchp_1",
      "name": "Primary CHW Pump 1",
      "tags": {
        "model": "pchp",
        "spaceRef": "plant"
      }
    }
  ]
}
```

### Equipment Models (tags.model)
- `chiller` - Chillers
- `pchp` - Primary Chilled Water Pumps
- `schp` - Secondary Chilled Water Pumps
- `cdp` - Condenser Water Pumps
- `ct` or `cooling_tower` - Cooling Towers

---

## 4. Historical Timeseries API

For charts like BuildingLoadGraph (24-hour trend).

### Endpoint
```
GET /api/sites/{site_id}/timeseries/query
```

### Request Body
```json
{
  "site_id": "jwmb",
  "device_id": "plant",
  "datapoints": ["power", "cooling_rate"],
  "start_timestamp": "2024-01-14T00:00:00Z",
  "end_timestamp": "2024-01-15T00:00:00Z",
  "resampling": "1h"
}
```

### Response Format
```json
{
  "data": [
    {
      "device_id": "plant",
      "datapoint": "power",
      "values": [
        { "timestamp": "2024-01-14T00:00:00Z", "value": 180 },
        { "timestamp": "2024-01-14T01:00:00Z", "value": 185 },
        { "timestamp": "2024-01-14T02:00:00Z", "value": 175 }
      ]
    },
    {
      "device_id": "plant",
      "datapoint": "cooling_rate",
      "values": [
        { "timestamp": "2024-01-14T00:00:00Z", "value": 245 },
        { "timestamp": "2024-01-14T01:00:00Z", "value": 250 },
        { "timestamp": "2024-01-14T02:00:00Z", "value": 240 }
      ]
    }
  ]
}
```

---

## 5. AFDD Alerts API

### Endpoint
```
GET /api/sites/{site_id}/afdd/alerts
```

### Response Format
```json
{
  "alerts": [
    {
      "id": 123,
      "fault_name": "Chiller Power Mismatch",
      "category": "water-side",
      "severity": "warning",
      "device_id": "chiller_1",
      "is_active": true,
      "active_at": "2024-01-15T08:30:00Z",
      "message": "Chiller 1 power reading differs from expected value"
    }
  ],
  "summary": {
    "water-side": { "critical": 0, "warning": 1, "info": 0 },
    "air-side": { "critical": 0, "warning": 0, "info": 2 },
    "electrical": { "critical": 0, "warning": 0, "info": 0 }
  }
}
```

---

## 6. Daily Energy Summary API

For EnergyUsageCard (Yesterday vs Today comparison).

### Endpoint
```
GET /api/sites/{site_id}/energy/daily
```

### Response Format
```json
{
  "yesterday": {
    "total": 12500,
    "plant": 8200,
    "air_side": 4300
  },
  "today": {
    "total": 10800,
    "plant": 7100,
    "air_side": 3700
  },
  "unit": "kWh"
}
```

---

## 7. WebSocket Real-Time Updates

For live data updates without polling.

### Connection
```
wss://api.example.com/realtime?site_id=jwmb
```

### Message Format (Server → Client)
```json
{
  "type": "update",
  "device_id": "plant",
  "datapoint": "power",
  "value": 188,
  "updated_at": "2024-01-15T10:31:00Z"
}
```

---

## 8. Site Configuration

Already defined in `config/sites.yaml`. Backend should read from this file or sync with it.

```yaml
sites:
  - site_id: jwmb
    site_name: JW Marriott Bangkok
    site_code: JWMB
    latitude: 13.7432
    longitude: 100.5489
    timezone: Asia/Bangkok
    database:
      supabase_url: https://xxx.supabase.co
      supabase_anon_key: xxx
      timescaledb_host: localhost
      timescaledb_port: 5432
```

---

## 9. Priority for Implementation

### Phase 1 (MVP)
1. Real-time data API (Supabase or TimescaleDB fallback)
2. Ontology/Equipment list API
3. Weather station data

### Phase 2
4. Historical timeseries API
5. Daily energy summary API

### Phase 3
6. AFDD alerts API
7. WebSocket real-time updates

---

## 10. Notes

- All temperatures stored in °F (frontend handles unit conversion)
- All timestamps in ISO 8601 format with timezone (UTC preferred)
- `status_read` uses 0/1 integer (not boolean) for consistency
- Flow rates must be >= 1 for plant diagram animation to work
- Equipment numbering starts at 1 (chiller_1, not chiller_0)
