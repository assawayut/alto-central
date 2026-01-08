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

| Source | Table/Collection | Purpose |
|--------|------------------|---------|
| Supabase | `latest_data` | Real-time sensor values (primary) |
| TimescaleDB | `aggregated_data` | Real-time fallback + historical timeseries |
| TimescaleDB | `daily_energy_data` | Daily aggregated energy data |
| MongoDB | `control.action_event` | Action events (chiller sequences, schedules) |

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
| `GET /api/v1/sites/{site_id}/timeseries/aggregated` | Pre-aggregated data (24h/7d/30d/today/yesterday) |
| `GET /api/v1/sites/{site_id}/timeseries/latest-from-history` | Latest values from TimescaleDB |

### Analytics

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/sites/{site_id}/analytics/plant-performance` | Plant performance scatter plot data |
| `GET /api/v1/sites/{site_id}/analytics/cooling-tower-tradeoff` | Chiller vs CT power trade-off data |

### Events

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/sites/{site_id}/events/` | All action events (MongoDB) |
| `GET /api/v1/sites/{site_id}/events/upcoming` | Upcoming events for timeline |

### AI-Powered Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/sites/{site_id}/ai-analytics/chart` | POST | Generate chart from natural language prompt |
| `/api/v1/sites/{site_id}/ai-analytics/chart/stream` | POST | Generate chart with SSE streaming progress |
| `/api/v1/sites/{site_id}/ai-analytics/chart/from-template/{template_id}` | POST | Generate chart from specific template |
| `/api/v1/sites/{site_id}/ai-analytics/templates` | GET | List available chart templates |
| `/api/v1/sites/{site_id}/ai-analytics/templates` | POST | Create new custom template |
| `/api/v1/sites/{site_id}/ai-analytics/templates/{template_id}` | GET | Get template details |
| `/api/v1/sites/{site_id}/ai-analytics/templates/{template_id}` | DELETE | Delete custom template |

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
- `period`: Time period - `24h`, `7d`, `30d`, `today`, `yesterday` (default: `24h`)
- `aggregation`: Aggregation level - `hourly`, `daily` (default: `hourly`)

> **Note:** `today` and `yesterday` use the site's local timezone (from sites.yaml)

### Plant Performance Analytics (`/analytics/plant-performance`)

```
GET /api/v1/sites/kspo/analytics/plant-performance?resolution=1h&start_date=2025-12-01&end_date=2025-12-28
```

```json
{
  "site_id": "kspo",
  "start_date": "2025-12-01",
  "end_date": "2025-12-28",
  "resolution": "1h",
  "filters": {
    "start_time": "00:00",
    "end_time": "23:59",
    "day_type": "all"
  },
  "count": 245,
  "data": [
    {
      "timestamp": "2025-12-27T08:00:00+07:00",
      "cooling_load": 206.93,
      "power": 183.4,
      "efficiency": 0.8863,
      "num_chillers": 1,
      "chiller_combination": "CH-5",
      "chs": 48.44,
      "cds": 80.57,
      "outdoor_wbt": 72.56,
      "outdoor_dbt": 85.37
    }
  ]
}
```

**Query parameters:**
- `start_date`, `end_date`: Date range (default: last 3 months)
- `resolution`: `1m`, `15m`, `1h` (default: `1h`)
- `start_time`, `end_time`: Filter by time of day (e.g., `09:00` - `18:00`)
- `day_type`: `all`, `weekdays`, `weekends` (default: `all`)

**Response fields:**
| Field | Unit | Description |
|-------|------|-------------|
| `cooling_load` | RT | Cooling load from `plant.cooling_rate` |
| `power` | kW | Plant power from `plant.power` |
| `efficiency` | kW/RT | Calculated as `power / cooling_load` |
| `num_chillers` | count | Number of running chillers |
| `chiller_combination` | string | Running chillers (e.g., "CH-1+CH-2") |
| `chs` | °F | Chilled water supply temp |
| `cds` | °F | Condenser water supply temp |
| `outdoor_wbt` | °F | Outdoor wet-bulb temp |
| `outdoor_dbt` | °F | Outdoor dry-bulb temp |

> **Note:** Points with `cooling_load < 10 RT` are excluded to reduce noise.

### Cooling Tower Trade-off Analytics (`/analytics/cooling-tower-tradeoff`)

```
GET /api/v1/sites/kspo/analytics/cooling-tower-tradeoff?resolution=15m&start_date=2025-10-01&end_date=2025-12-28
```

```json
{
  "site_id": "kspo",
  "start_date": "2025-10-01",
  "end_date": "2025-12-28",
  "resolution": "15m",
  "filters": {
    "start_time": "00:00",
    "end_time": "23:59",
    "day_type": "all"
  },
  "count": 2500,
  "data": [
    {
      "timestamp": "2025-10-15T14:00:00+07:00",
      "cds": 85.2,
      "power_chillers": 950,
      "power_cts": 120,
      "outdoor_wbt": 78.5,
      "cooling_load": 1850
    }
  ]
}
```

**Query parameters:** Same as plant-performance endpoint.

**Response fields:**
| Field | Unit | Description |
|-------|------|-------------|
| `cds` | °F | Condenser water supply temp (X-axis) |
| `power_chillers` | kW | Total chiller power |
| `power_cts` | kW | Total cooling tower power |
| `outdoor_wbt` | °F | Outdoor wet-bulb temp (for filtering) |
| `cooling_load` | RT | Cooling load (for filtering) |

> **Note:** Points with `cooling_load < 100 RT`, `power_chillers <= 0`, or `power_cts <= 0` are excluded.

### Action Events (`/events/`)

```
GET /api/v1/sites/kspo/events/?status=all&limit=20
```

```json
{
  "site_id": "kspo",
  "events": [
    {
      "event_id": "evt_001",
      "event_type": "start_chiller_sequence",
      "title": "Start CH-1",
      "description": null,
      "scheduled_time": "2025-01-15T07:00:00+07:00",
      "status": "pending",
      "equipment": ["chiller_1"],
      "source": "automation"
    }
  ],
  "total_count": 1
}
```

**Query parameters:**
- `status`: Filter by status - `all`, `pending`, `in-progress`, `completed`, `failed` (default: `all`)
- `limit`: Max events to return (default: `20`, max: `100`)

**Event types:** `start_chiller_sequence`, `stop_chiller_sequence`, `schedule`

### AI Analytics - Generate Chart (`/ai-analytics/chart`)

```
POST /api/v1/sites/kspo/ai-analytics/chart
Content-Type: application/json

{
  "prompt": "Show me plant efficiency vs cooling load for the last 2 weeks",
  "parameters": {
    "resolution": "1h"
  }
}
```

```json
{
  "chart_id": "a1b2c3d4",
  "plotly_spec": {
    "data": [
      {
        "type": "scatter",
        "mode": "markers",
        "name": "Operating Points",
        "x": [150, 200, 250, 300],
        "y": [0.75, 0.72, 0.70, 0.68],
        "marker": {"size": 6, "opacity": 0.7}
      }
    ],
    "layout": {
      "title": {"text": "Plant Efficiency vs Cooling Load"},
      "xaxis": {"title": "Cooling Load (RT)"},
      "yaxis": {"title": "Efficiency (kW/RT)"}
    }
  },
  "template_used": "plant_efficiency_vs_load",
  "template_match_confidence": 0.85,
  "data_sources": ["timescale:plant"],
  "query_summary": "Queried 336 data points",
  "message": "Generated chart using 'Plant Efficiency vs Cooling Load' template."
}
```

**Request fields:**
- `prompt`: Natural language description of the chart you want
- `parameters`: Optional overrides (date_range, resolution, device, etc.)

**Response fields:**
- `plotly_spec`: Complete Plotly.js specification - render with `Plotly.newPlot(div, spec.data, spec.layout)`
- `template_used`: Template ID if matched, null if AI-generated
- `template_match_confidence`: Confidence score (0-1) if template matched
- `data_sources`: Data sources queried
- `message`: Human-readable explanation

**Example prompts:**
| Prompt | Description |
|--------|-------------|
| "Show plant efficiency vs cooling load" | Scatter plot of kW/RT vs RT |
| "Compare chiller_1 and chiller_2 power" | Multi-line comparison |
| "Chiller_1 efficiency today vs yesterday" | Period comparison (x-axis: hour of day) |
| "Plant efficiency when only chiller_2 running" | Filtered by equipment status |
| "Power trend for the last 24 hours" | Line chart time series |

**AI Tool Features:**

The AI (Claude Sonnet) uses these tools:

| Tool | Description |
|------|-------------|
| `query_and_chart` | Combined query + chart for simple requests |
| `labeled_scatter_chart` | **Server-side** labeled scatter (chiller count/combo) - fastest! |
| `query_timeseries` | Query single device historical data |
| `batch_query_timeseries` | Query multiple devices in parallel |
| `create_scatter_chart` | Scatter with optional color gradient |
| `create_multi_trace_scatter` | Manual scatter with labeled groups |
| `create_line_chart` | Time series trends |
| `create_bar_chart` | Categorical comparisons |

**Filtering options** (via `query_and_chart`):

| Feature | Example | Description |
|---------|---------|-------------|
| Period comparison | `compare_periods: ["today", "yesterday"]` | Compare same metric across days (x-axis = hour) |
| Equipment filter | `filters: {only_running: ["chiller_2"]}` | Only include data when device is running |
| Exclusion filter | `filters: {not_running: ["chiller_1"]}` | Exclude data when device is running |
| Chiller count | `filters: {num_chillers_running: 2}` | Filter by number of chillers running |
| Load filter | `filters: {min_cooling_load: 100}` | Minimum cooling load threshold |
| Time filter | `filters: {time_of_day: {start: 8, end: 18}}` | Filter by working hours |

**Complex labeling** (AI handles automatically):

| Labeling Type | Tool Used | Example |
|---------------|-----------|---------|
| By continuous value | `create_scatter_chart` with `color_field` | Color by wetbulb temperature |
| By category | `create_multi_trace_scatter` | Label by chiller count (1, 2, 3 chillers) |
| By combination | `create_multi_trace_scatter` | Label by which chillers are running |

**Device ID patterns:**
- `plant` - Aggregate plant data
- `chiller_{N}` - Individual chillers (chiller_1, chiller_2, ...)
- `ct_{N}` - Cooling towers
- `pchp_{N}`, `schp_{N}`, `cdp_{N}` - Pumps
- `chilled_water_loop`, `condenser_water_loop` - Water loops
- `outdoor_weather_station` - Weather data

### AI Analytics - List Templates (`/ai-analytics/templates`)

```
GET /api/v1/sites/kspo/ai-analytics/templates?category=performance
```

```json
{
  "templates": [
    {
      "template_id": "plant_efficiency_vs_load",
      "title": "Plant Efficiency vs Cooling Load",
      "description": "Scatter plot of kW/RT vs cooling load",
      "category": "performance",
      "created_by": "system",
      "usage_count": 42,
      "tags": ["efficiency", "scatter", "plant"]
    }
  ],
  "total_count": 4,
  "builtin_count": 4,
  "custom_count": 0
}
```

**Query parameters:**
- `category`: Filter by category - `performance`, `energy`, `equipment`, `comparison`, `forecast`
- `include_builtin`: Include system templates (default: true)
- `include_custom`: Include AI/user-created templates (default: true)

**Builtin templates:**
| Template ID | Chart Type | Description |
|-------------|------------|-------------|
| `plant_efficiency_vs_load` | Scatter | Plant kW/RT efficiency vs cooling load |
| `chiller_power_trend` | Line | Chiller power consumption over time |
| `daily_energy_profile` | Bar | Average hourly energy consumption |
| `temperature_comparison` | Multi-line | Supply/return temps with delta-T |

## Project Structure

```
alto-central-backend/
├── app/
│   ├── api/v1/              # API endpoints
│   │   ├── realtime.py      # Real-time data endpoints
│   │   ├── energy.py        # Energy data endpoints
│   │   ├── timeseries.py    # Historical queries
│   │   ├── analytics.py     # Plant performance analytics
│   │   ├── ai_analytics.py  # AI-powered chart generation
│   │   ├── events.py        # Action events (MongoDB)
│   │   └── sites.py         # Sites listing
│   ├── analytics/           # AI analytics module
│   │   ├── templates/       # Chart template system
│   │   │   ├── schema.py    # Template Pydantic models
│   │   │   ├── manager.py   # Template CRUD operations
│   │   │   └── matcher.py   # NL prompt matching
│   │   ├── charts/          # Chart generation
│   │   │   └── plotly_builder.py  # Plotly spec builder
│   │   └── service.py       # Main orchestrator
│   ├── llm/                 # LLM integration
│   │   ├── client.py        # Anthropic client wrapper
│   │   ├── prompts/         # System prompts
│   │   └── tools/           # AI tool definitions
│   │       ├── data_tools.py    # Data querying tools
│   │       ├── chart_tools.py   # Chart creation tools
│   │       └── template_tools.py # Template management
│   ├── config/              # Configuration loading
│   ├── core/                # Core utilities
│   ├── db/                  # Database connections
│   │   └── connections/
│   │       ├── supabase.py    # Supabase client (httpx)
│   │       ├── timescale.py   # TimescaleDB client (asyncpg)
│   │       └── mongodb.py     # MongoDB client (motor)
│   ├── models/              # Pydantic schemas
│   └── main.py              # FastAPI app
├── config/                  # Shared config (symlink to ../config)
├── templates/               # Chart templates (YAML)
│   ├── builtin/             # System templates
│   └── custom/              # AI-generated templates
├── docker/                  # Docker configuration
└── tests/                   # Test suite
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
