# Alto Central Backend

Backend API for the Alto Central HVAC monitoring system. Provides real-time sensor data, historical energy data, and equipment status for multiple building sites.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Alto Central Backend                         │
│                     Port: 8642                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  External Data Sources (READ-ONLY)                              │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │    Supabase      │    │   TimescaleDB    │                   │
│  │  (latest_data)   │    │ (aggregated_data)│                   │
│  │                  │    │ (daily_energy)   │                   │
│  │  Primary source  │    │  Fallback for    │                   │
│  │  for real-time   │    │  real-time +     │                   │
│  │                  │    │  historical      │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
│  Per-Site Configuration: config/sites.yaml                      │
│  ⚠️  READ-ONLY connections - NEVER write to production          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Sources

| Source | Table | Purpose |
|--------|-------|---------|
| Supabase | `latest_data` | Real-time sensor values (primary) |
| TimescaleDB | `aggregated_data` | Real-time fallback + historical timeseries |
| TimescaleDB | `daily_energy_data` | Daily aggregated energy data |

**Priority for real-time data:**
1. Supabase `latest_data` (if configured for site)
2. TimescaleDB `aggregated_data` with latest timestamp (fallback)
3. Empty response (if neither available)

## Quick Start

### Prerequisites

- Python 3.11+
- Network access to production databases (Supabase/TimescaleDB)

### Development Setup

```bash
cd alto-central/alto-central-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the API (port 8642)
uvicorn app.main:app --reload --port 8642
```

### View API Documentation

- Swagger UI: http://localhost:8642/docs
- ReDoc: http://localhost:8642/redoc

## API Endpoints

### Sites

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/sites` | List all configured sites |

### Real-time Data

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/sites/{site_id}/realtime/latest` | All devices latest values |
| `GET /api/v1/sites/{site_id}/realtime/latest/{device_id}` | Specific device values |
| `GET /api/v1/sites/{site_id}/realtime/plant` | Plant-level summary |

### Energy Data

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/sites/{site_id}/energy/daily` | Yesterday vs today comparison |
| `GET /api/v1/sites/{site_id}/energy/monthly` | Monthly summary (stub) |

### Historical Data

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/sites/{site_id}/timeseries/query` | Custom timeseries query with resampling |
| `GET /api/v1/sites/{site_id}/timeseries/aggregated` | Pre-aggregated data (24h/7d/30d) |
| `GET /api/v1/sites/{site_id}/timeseries/latest-from-history` | Latest values from TimescaleDB |

## Site Configuration

Sites are configured in `config/sites.yaml` (shared with frontend):

```yaml
sites:
  - site_id: kspo
    site_name: Bank of Ayudhya (Krungsri) - Phloen Chit Office
    site_code: KSPO
    latitude: 13.7430946
    longitude: 100.5444255
    timezone: Asia/Bangkok
    hvac_type: water          # water = water-side only, air = includes air-side
    building_type: office
    database:
      timescaledb:
        host: 10.144.168.147
        port: 5432
        database: postgres
        user: postgres
        password: xxx
      supabase:
        url: http://10.144.168.147:8000
        anon_key: eyJhbGci...
```

**HVAC Types:**
- `water`: Water-side only (chillers, cooling towers, pumps). Energy API returns `air_side: null`
- `air`: Includes air-side equipment (AHUs). Energy API returns both plant and air-side

## Response Examples

### Real-time Latest (`/realtime/latest`)

```json
{
  "site_id": "kspo",
  "timestamp": "2025-12-27T13:09:34.259688",
  "devices": {
    "chiller_1": {
      "power": {"value": 607.05, "updated_at": "2025-12-27T13:08:51+00:00"},
      "cooling_rate": {"value": 1032.59, "updated_at": "2025-12-27T13:08:51+00:00"},
      "efficiency": {"value": 0.586, "updated_at": "2025-12-27T13:08:51+00:00"},
      "status_read": {"value": 1, "updated_at": "2025-12-27T13:08:51+00:00"}
    },
    "plant": {
      "power": {"value": 1.10, "updated_at": "2025-12-27T13:09:31+00:00"},
      "cooling_rate": {"value": 0.83, "updated_at": "2025-12-27T13:09:31+00:00"}
    }
  }
}
```

### Energy Daily (`/energy/daily`)

```json
{
  "site_id": "kspo",
  "yesterday": {
    "total": 6859.58,
    "plant": 6859.58,
    "air_side": null
  },
  "today": {
    "total": 773.36,
    "plant": 773.36,
    "air_side": null
  },
  "unit": "kWh"
}
```

### Plant Summary (`/realtime/plant`)

```json
{
  "site_id": "kspo",
  "plant": {
    "power_kw": 1.10,
    "cooling_rate_rt": 0.83,
    "efficiency_kw_rt": 0,
    "heat_reject_rt": -0.37
  },
  "chilled_water": {
    "supply_temp_f": 53.47,
    "return_temp_f": 54.99,
    "delta_t": 1.53,
    "flow_rate_gpm": 0
  },
  "condenser_water": {
    "supply_temp_f": 81.0,
    "return_temp_f": 82.99,
    "delta_t": 1.99,
    "flow_rate_gpm": -4.46
  },
  "weather": {
    "drybulb_temp_f": 88.07,
    "wetbulb_temp_f": 72.70,
    "humidity_pct": 48.28
  }
}
```

### Timeseries Aggregated (`/timeseries/aggregated`)

```
GET /api/v1/sites/kspo/timeseries/aggregated?device_id=plant&datapoint=power&period=24h&aggregation=hourly
```

```json
{
  "site_id": "kspo",
  "device_id": "plant",
  "datapoint": "power",
  "period": "24h",
  "aggregation": "hourly",
  "data": [
    {"timestamp": "2025-12-26T07:00:00+00:00", "value": 567.53},
    {"timestamp": "2025-12-26T08:00:00+00:00", "value": 566.95},
    {"timestamp": "2025-12-26T09:00:00+00:00", "value": 575.45}
  ]
}
```

**Query parameters:**
- `device_id`: Device identifier (default: `plant`)
- `datapoint`: Datapoint name (default: `power`)
- `period`: Time period - `24h`, `7d`, `30d` (default: `24h`)
- `aggregation`: Aggregation level - `hourly`, `daily` (default: `hourly`)

## Project Structure

```
alto-central-backend/
├── app/
│   ├── api/v1/           # API endpoints
│   │   ├── realtime.py   # Real-time data endpoints
│   │   ├── energy.py     # Energy data endpoints
│   │   ├── sites.py      # Sites listing
│   │   └── timeseries.py # Historical queries
│   ├── config/           # Configuration loading
│   │   ├── sites.py      # sites.yaml parser
│   │   └── settings.py   # App settings
│   ├── core/             # Core utilities
│   ├── db/               # Database connections
│   │   └── connections/
│   │       ├── supabase.py    # Supabase client (httpx)
│   │       └── timescale.py   # TimescaleDB client (asyncpg)
│   ├── models/           # Pydantic schemas
│   └── main.py           # FastAPI app
├── config/               # Shared config (symlink to ../config)
├── docker/               # Docker configuration
└── tests/                # Test suite
```

## Dependencies

Key packages:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `asyncpg` - Async PostgreSQL driver (TimescaleDB)
- `httpx` - Async HTTP client (Supabase REST API)
- `pydantic` - Data validation
- `pyyaml` - YAML config parsing

## License

Proprietary - Alto Central
