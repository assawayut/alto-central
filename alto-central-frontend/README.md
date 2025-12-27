# Alto Central Frontend

A centralized HVAC (Heating, Ventilation, and Air Conditioning) operation monitoring system. This is a standalone frontend application that displays real-time data from multiple building sites, focusing primarily on chiller plant operations.

## Project Overview

### Purpose
- Display locations of all HVAC systems across multiple sites on an interactive map
- Provide real-time monitoring dashboards for each site's chiller plant
- Future: ML optimization features, air-side monitoring, hotel guest room controls

### Current Status
- **Site Map Page**: Interactive MapLibre map with custom site markers (card + pin design)
- **Chiller Plant Dashboard**: Real-time monitoring with animated water flow diagram
- **Site Config**: YAML-based configuration shared between frontend and backend
- **Mock Data**: All real-time data is mocked for standalone frontend development

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS 3 with CSS variables
- **Maps**: MapLibre GL JS (replaced Leaflet)
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
├── alto-central-frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/         # Header, PageLayout
│   │   │   └── ui/             # Reusable UI (card, badge, button, etc.)
│   │   ├── config/
│   │   │   └── sites.ts        # Loads from YAML, exports SiteConfig types
│   │   ├── contexts/
│   │   │   └── DeviceContext.tsx
│   │   ├── features/
│   │   │   ├── afdd/           # AFDD alerts (mock)
│   │   │   ├── auth/           # Authentication (mock)
│   │   │   ├── ontology/       # Equipment entities (mock)
│   │   │   ├── realtime/       # Real-time data (mock)
│   │   │   └── timeseries/     # Historical data (mock)
│   │   ├── pages/
│   │   │   ├── ChillerPlant/   # Dashboard page
│   │   │   │   ├── components/
│   │   │   │   │   ├── BuildingLoadGraph.tsx
│   │   │   │   │   ├── EfficiencyCard.tsx
│   │   │   │   │   ├── EnergyUsageCard.tsx
│   │   │   │   │   ├── PlantDiagram.tsx
│   │   │   │   │   ├── PlantEquipmentCard.tsx
│   │   │   │   │   ├── PowerCard.tsx
│   │   │   │   │   ├── SystemAlertCard.tsx
│   │   │   │   │   ├── UpcomingEventsCard.tsx
│   │   │   │   │   └── WeatherStationCard.tsx
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

## Site Configuration (IMPORTANT)

Sites are configured in a **shared YAML file** that both frontend and backend can use:

**Location**: `alto-central/config/sites.yaml`

```yaml
map:
  center:
    latitude: 13.7563
    longitude: 100.5018
  zoom: 6

sites:
  - site_id: jwmb
    site_name: JW Marriott Bangkok
    site_code: JWMB           # Shown on map marker
    latitude: 13.7432
    longitude: 100.5489
    timezone: Asia/Bangkok
    # Optional database config for backend:
    # database:
    #   timescaledb_host: localhost
    #   timescaledb_port: 5432
    #   supabase_url: https://xxx.supabase.co
```

**To add a new site**: Edit `config/sites.yaml` - the map will automatically update.

**Frontend usage**:
```typescript
import { sites, getSiteById, defaultMapCenter } from '@/config/sites';
```

## Key Components

### Pages

1. **SiteMap** (`/`)
   - MapLibre GL map with custom markers (white card + orange pin)
   - Each marker shows: site_code, EUI value
   - Click marker → navigate to `/site/:siteId`
   - Overview stats cards at top

2. **ChillerPlant** (`/site/:siteId`)
   - 3-column layout:
     - **Left**: EnergyUsageCard, BuildingLoadGraph, SystemAlertCard
     - **Center**: Efficiency + Power + Weather cards, then Equipment Status + Plant Diagram
     - **Right**: UpcomingEventsCard (maintenance timeline)

### Dashboard Components

| Component | Description |
|-----------|-------------|
| `EnergyUsageCard` | Yesterday vs Today: Total, Plant, Air-Side (kWh) + DBT/RH |
| `PowerCard` | 3 sections: Plant Power (kW), Cooling Load (RT), Part-Load (%) |
| `WeatherStationCard` | DBT, WBT, Humidity - inline values |
| `UpcomingEventsCard` | Horizontal date tabs + vertical event list, color-coded |
| `PlantDiagram` | Animated water flow (CHW blue, CDW orange) |
| `PlantEquipmentCard` | Equipment grid with status indicators |
| `EfficiencyCard` | Gauge with Excellent/Good/Fair/Improve thresholds |
| `BuildingLoadGraph` | ECharts line chart for power & cooling load |

### Mock Features

All features in `src/features/` are mocked:

- **realtime**: `useRealtime()` → `getValue(deviceId, datapoint)`, `getUnit()`
- **ontology**: `useOntologyEntities()` → equipment list (chiller, pchp, cdp, ct)
- **afdd**: `useAFDDAlertSummary()` → alert categories
- **timeseries**: `fetchAggregatedData()` → historical data
- **auth**: `useAuth()`, `getSiteId()` → mock auth context

## Development

```bash
cd alto-central-frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

## Important Implementation Notes

### MapLibre Setup

The map uses MapLibre GL JS with custom HTML markers:
- **Style**: Uses demo tiles (replace `MAPTILER_KEY` in `MapView.tsx` for production)
- **Markers**: Custom DOM elements with card + pin design
- **Config**: Reads from `@config/sites.yaml` via Vite plugin

### Plant Diagram Animation

Animation triggers when `flow_rate >= 1` in `src/features/realtime/index.ts`:
```typescript
chilled_water_loop: { flow_rate: 381 },    // >= 1 enables CHW animation
condenser_water_loop: { flow_rate: 7 },    // >= 1 enables CDW animation
```

### CSS Variables (globals.css)

Key colors:
- `--primary`: #0d6de3 (blue)
- `--primary-dark`: #0654a7
- `--success`: #14b8b2 (teal)
- `--warning`: #fecb52 (yellow)
- `--danger`: #ef4134 (red)

### Equipment Status Values

```typescript
status_read: 0  // Standby (gray)
status_read: 1  // Running (blue border)
alarm: 1        // Alarm state (red)
```

## Future Development

### Next Steps
1. **Backend Integration**: Replace mock features with real API calls
2. **MapTiler API Key**: Get key from maptiler.com for production map tiles
3. **Air-Side Tab**: Implement air handling unit monitoring
4. **Events API**: Connect UpcomingEventsCard to real scheduling system
5. **WebSocket**: Real-time data updates

### Backend Requirements
When implementing backend, it should provide:
- Real-time WebSocket for live sensor data
- REST API for ontology (equipment) queries
- TimescaleDB API for historical timeseries
- AFDD API for fault detection alerts
- Events/Scheduling API for maintenance

### Files to Modify for Backend Integration

1. `src/features/realtime/index.ts` - Replace mock with WebSocket
2. `src/features/ontology/index.ts` - Replace mock with API calls
3. `src/features/afdd/hooks.ts` - Replace mock with API calls
4. `src/features/timeseries/index.ts` - Replace mock with API calls
5. `config/sites.yaml` - Add database connection strings

## Component Origins

Most dashboard components were copied from `alto-cero-interface` project:
- Removed Supabase real-time subscriptions
- Replaced with mock data hooks
- Some TypeScript errors exist (pre-existing, doesn't affect runtime)

## Troubleshooting

1. **Map not showing**: Check if `maplibre-gl` CSS is imported in `MapView.tsx`
2. **Animation not working**: Ensure `flow_rate >= 1` in realtime mock data
3. **YAML import error**: Check `vite.config.ts` has yaml plugin and `@config` alias
4. **Site not appearing**: Add site to `config/sites.yaml` and refresh

## Git Repository

- **Remote**: https://github.com/assawayut/alto-central.git
- **Excluded from git**: `.claude/`, `alto-cero-interfacec-src-file/`, `node_modules/`
