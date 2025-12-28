# Alto Central Frontend

A centralized HVAC (Heating, Ventilation, and Air Conditioning) operation monitoring system. This frontend application displays real-time data from multiple building sites, focusing primarily on chiller plant operations.

## Project Overview

### Purpose
- Display locations of all HVAC systems across multiple sites on an interactive map
- Provide real-time monitoring dashboards for each site's chiller plant
- Future: ML optimization features, air-side monitoring, hotel guest room controls

### Current Status
- **Site Map Page**: Interactive MapLibre map with custom site markers (card + pin design)
- **Chiller Plant Dashboard**: Real-time monitoring with animated water flow diagram
- **Site Config**: YAML-based configuration shared between frontend and backend
- **Backend Integration**: Connected to real API for real-time data (polling every 10s)

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS 3 with CSS variables
- **Maps**: MapLibre GL JS with OpenStreetMap tiles
- **Charts**: ECharts + echarts-for-react
- **Icons**: Lucide React, React Icons
- **Date/Time**: Luxon
- **Routing**: React Router DOM v6
- **Config**: YAML (`@modyfi/vite-plugin-yaml`)

## Project Structure

```
alto-central/
├── config/
│   └── sites.yaml              # SHARED site config (frontend + backend)
├── docs/
│   ├── BACKEND_REQUIREMENTS.md # API requirements doc
│   └── FRONTEND_API_INTEGRATION.md # Integration guide
├── alto-central-frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/         # Header, PageLayout
│   │   │   └── ui/             # Reusable UI (card, badge, button, table, etc.)
│   │   ├── config/
│   │   │   ├── api.ts          # API endpoints and config
│   │   │   └── sites.ts        # Loads from YAML, exports SiteConfig types
│   │   ├── contexts/
│   │   │   └── DeviceContext.tsx
│   │   ├── features/
│   │   │   ├── afdd/           # AFDD alerts (mock)
│   │   │   ├── auth/           # Authentication (mock)
│   │   │   ├── ontology/       # Equipment entities (mock - not used)
│   │   │   ├── realtime/       # Real-time data (API integrated)
│   │   │   └── timeseries/     # Historical data (mock)
│   │   ├── pages/
│   │   │   ├── ChillerPlant/   # Dashboard page
│   │   │   │   ├── components/
│   │   │   │   │   ├── BuildingLoadGraph.tsx
│   │   │   │   │   ├── EfficiencyCard.tsx
│   │   │   │   │   ├── EnergyUsageCard.tsx
│   │   │   │   │   ├── PlantDiagram.tsx
│   │   │   │   │   ├── PlantEquipmentCard.tsx
│   │   │   │   │   ├── PlantEquipmentModal.tsx
│   │   │   │   │   ├── PowerCard.tsx
│   │   │   │   │   ├── SystemAlertCard.tsx
│   │   │   │   │   ├── UpcomingEventsCard.tsx
│   │   │   │   │   ├── WeatherStationCard.tsx
│   │   │   │   │   ├── DataAnalyticsCard.tsx
│   │   │   │   │   ├── DataAnalyticsModal.tsx
│   │   │   │   │   └── OptimizationCard.tsx
│   │   │   │   └── index.tsx
│   │   │   └── SiteMap/        # Landing page with map
│   │   │       ├── components/
│   │   │       │   ├── BuildingCard.tsx
│   │   │       │   └── MapView.tsx   # MapLibre implementation
│   │   │       └── index.tsx
│   │   ├── types/
│   │   │   ├── yaml.d.ts       # YAML import declarations
│   │   │   └── ...
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   └── globals.css
│   ├── vite.config.ts          # Includes YAML plugin, @config alias
│   └── tsconfig.json           # Includes @config path
└── .gitignore
```

## Site Configuration

Sites are configured in a **shared YAML file** that both frontend and backend use:

**Location**: `alto-central/config/sites.yaml`

```yaml
map:
  center:
    latitude: 13.7563
    longitude: 100.5018
  zoom: 6

sites:
  - site_id: kspo
    site_name: Bank of Ayudhya (Krungsri) - Phloen Chit Office
    site_code: KSPO
    latitude: 13.7430946
    longitude: 100.5444255
    timezone: Asia/Bangkok
    hvac_type: water          # water, air, both, water_air_integration, hotel, etc.
    building_type: office
    design_capacity_rt: 3000  # For part-load calculation (optional)
    database:
      timescaledb:
        host: 10.144.168.147
        port: 5433
      supabase:
        url: http://10.144.168.147:8000
```

**To add a new site**: Edit `config/sites.yaml` - both frontend map and backend will use it.

## API Integration

### Backend API
- **Base URL**: `http://localhost:8642/api/v1`
- **Polling Interval**: 10 seconds

### Endpoints Used
| Endpoint | Description |
|----------|-------------|
| `GET /sites` | List all sites |
| `GET /sites/{siteId}/realtime/latest` | Real-time device data |
| `GET /sites/{siteId}/energy/daily` | Yesterday vs Today energy |
| `GET /sites/{siteId}/timeseries/aggregated` | Historical data for charts |
| `GET /sites/{siteId}/analytics/plant-performance` | Plant performance scatter plot data |

### Timeseries Query Parameters
| Parameter | Default | Options | Description |
|-----------|---------|---------|-------------|
| `device_id` | `plant` | Any device ID | Device to query |
| `datapoint` | `power` | Any datapoint | Datapoint to query |
| `period` | `24h` | `24h`, `7d`, `30d`, `today`, `yesterday` | Time range |
| `aggregation` | `hourly` | `hourly`, `daily` | Aggregation level |

### Plant Performance Analytics Parameters
| Parameter | Default | Options | Description |
|-----------|---------|---------|-------------|
| `start_date` | - | `YYYY-MM-DD` | Start date for query |
| `end_date` | - | `YYYY-MM-DD` | End date for query |
| `resolution` | `1h` | `1m`, `15m`, `1h` | Data resolution |
| `start_time` | `00:00` | `HH:MM` | Filter by time of day (start) |
| `end_time` | `23:59` | `HH:MM` | Filter by time of day (end) |
| `day_type` | `all` | `all`, `weekdays`, `weekends` | Filter by day type |

### Key Datapoints

**Plant Level** (`device_id: plant`):
- `power` - Total plant power (kW)
- `cooling_rate` - Cooling load (RT)
- `efficiency` - Plant efficiency (kW/RT)
- `running_capacity` - Part-load percentage (%)
- `target_chw_setpoint` - CHW setpoint (°F)
- `efficiency_ch` / `efficiency_chiller` - Chiller group efficiency
- `efficiency_pchp`, `efficiency_cdp`, `efficiency_ct` - Equipment group efficiencies

**Water Loops**:
- `chilled_water_loop`: supply/return temps, flow_rate
- `condenser_water_loop`: supply/return temps, flow_rate

**Equipment** (`chiller_1`, `pchp_1`, `cdp_1`, `ct_1`, etc.):
- `status_read` - 0=standby, 1=running
- `alarm` - 0=normal, 1=alarm
- `power` - Device power (kW)
- `frequency_read` - VFD frequency (Hz)
- `percentage_rla` - Chiller RLA (%)

**Weather** (`outdoor_weather_station`):
- `drybulb_temperature`, `wetbulb_temperature`, `humidity`

## Key Components

### Pages

1. **SiteMap** (`/`)
   - MapLibre GL map with OpenStreetMap tiles
   - Custom markers showing site_code
   - Click marker → navigate to `/site/:siteId`

2. **ChillerPlant** (`/site/:siteId`)
   - Wrapped in `RealtimeProvider` for API data
   - 3-column layout:
     - **Left**: EnergyUsageCard, BuildingLoadGraph, SystemAlertCard
     - **Center**: Efficiency + Power + Weather cards, Equipment Status + Plant Diagram
     - **Right**: DataAnalyticsCard, OptimizationCard
   - UpcomingEventsCard in header row
   - Air-Side tab hidden when `hvac_type: water`

### Dashboard Components

| Component | Data Source |
|-----------|-------------|
| `EnergyUsageCard` | `/energy/daily` API + realtime weather |
| `BuildingLoadGraph` | `/timeseries/aggregated` API (plant power + cooling_rate, 24h hourly) |
| `PowerCard` | `plant.power`, `plant.cooling_rate`, `plant.running_capacity` |
| `WeatherStationCard` | `outdoor_weather_station.*` |
| `PlantDiagram` | Water loop temps, `plant.target_chw_setpoint` |
| `PlantEquipmentCard` | Derived from realtime devices (`chiller_*`, `pchp_*`, etc.) |
| `PlantEquipmentModal` | Device details with efficiency from `plant.efficiency_*` |
| `EfficiencyCard` | `plant.efficiency` |
| `DataAnalyticsCard` | Opens DataAnalyticsModal |
| `DataAnalyticsModal` | `/analytics/plant-performance` API (ECharts scatter plot) |
| `OptimizationCard` | Placeholder for future ML optimization features |

## Development

```bash
cd alto-central-frontend

# Install dependencies
npm install

# Start dev server (requires backend running on port 8642)
npm run dev

# Build for production
npm run build
```

### Environment Variables (optional)
Create `.env` file:
```
VITE_API_BASE_URL=http://localhost:8642/api/v1
```

## Important Implementation Notes

### Realtime Data Flow
1. `RealtimeProvider` wraps ChillerPlant page
2. Fetches from `/sites/{siteId}/realtime/latest` every 10 seconds
3. Components use `useRealtime()` hook → `getValue(deviceId, datapoint)`
4. Equipment list derived from device IDs in response (e.g., `chiller_1`, `pchp_4`)

### Plant Diagram Animation
Animation triggers when `flow_rate >= 1`:
```typescript
chilled_water_loop.flow_rate >= 1    // Enables CHW animation
condenser_water_loop.flow_rate >= 1  // Enables CDW animation
```

### Equipment Status Display
```typescript
status_read: 0  // Standby (gray)
status_read: 1  // Running (green border)
alarm: 1        // Alarm state (red)
```

### HVAC Type Handling
When `hvac_type: water` in site config:
- Air-Side tab is hidden
- Air-Side row hidden in EnergyUsageCard

## Troubleshooting

1. **No data showing**: Check backend is running on port 8642
2. **Map not loading**: OpenStreetMap tiles should work without API key
3. **Equipment not showing**: Check device IDs match pattern (`chiller_`, `pchp_`, `cdp_`, `ct_`)
4. **Animation not working**: Ensure `flow_rate >= 1` from API
5. **YAML import error**: Check `vite.config.ts` has yaml plugin

## Git Repository

- **Remote**: https://github.com/assawayut/alto-central.git
