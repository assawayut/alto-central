# Alto Central Frontend

A centralized HVAC (Heating, Ventilation, and Air Conditioning) operation monitoring system. This is a standalone frontend application that displays real-time data from multiple building sites, focusing primarily on chiller plant operations.

## Project Overview

### Purpose
- Display locations of all HVAC systems across multiple sites on a map
- Provide real-time monitoring dashboards for each site's chiller plant
- Future: ML optimization features, air-side monitoring, hotel guest room controls

### Current Status
- **Site Map Page**: Interactive map showing building locations (using Leaflet)
- **Chiller Plant Dashboard**: Real-time monitoring with animated water flow diagram
- **Mock Data**: All data is currently mocked for standalone frontend development

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS 3 with CSS variables
- **Maps**: Leaflet + react-leaflet
- **Charts**: ECharts + echarts-for-react
- **Icons**: Lucide React, React Icons
- **Date/Time**: Luxon
- **Routing**: React Router DOM v6

## Project Structure

```
alto-central-frontend/
├── src/
│   ├── components/
│   │   ├── layout/          # Header, PageLayout
│   │   └── ui/              # Reusable UI components (card, badge, button, etc.)
│   ├── contexts/
│   │   └── DeviceContext.tsx  # Equipment/maintenance context
│   ├── data/
│   │   └── mockData.ts      # Mock site data
│   ├── features/
│   │   ├── afdd/            # Automated Fault Detection & Diagnostics (mock)
│   │   ├── auth/            # Authentication (mock)
│   │   ├── ontology/        # Equipment entity management (mock)
│   │   ├── realtime/        # Real-time data provider (mock)
│   │   └── timeseries/      # Historical data (mock)
│   ├── pages/
│   │   ├── ChillerPlant/    # Chiller plant dashboard
│   │   │   ├── components/  # Dashboard components
│   │   │   │   ├── BuildingLoadGraph.tsx
│   │   │   │   ├── EfficiencyCard.tsx
│   │   │   │   ├── PlantDiagram.tsx      # Animated water flow diagram
│   │   │   │   ├── PlantEquipmentCard.tsx
│   │   │   │   ├── PowerCard.tsx
│   │   │   │   ├── SystemAlertCard.tsx
│   │   │   │   └── WeatherStationCard.tsx
│   │   │   └── index.tsx
│   │   └── SiteMap/         # Landing page with map
│   │       ├── components/
│   │       │   ├── BuildingCard.tsx
│   │       │   └── MapView.tsx
│   │       └── index.tsx
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Utility functions
│   ├── App.tsx
│   ├── router.tsx
│   ├── main.tsx
│   └── globals.css          # Global styles with CSS variables
├── public/
│   └── images/equipment/    # Equipment images (chillers, pumps, etc.)
└── package.json
```

## Key Components

### Pages

1. **SiteMap** (`/`)
   - Landing page with interactive Leaflet map
   - Shows all building locations as markers
   - Click marker to navigate to site dashboard

2. **ChillerPlant** (`/site/:siteId`)
   - 3-column layout:
     - Left: BuildingLoadGraph, SystemAlertCard
     - Center: Efficiency/Power/Weather cards + Equipment Status + Plant Diagram
     - Right: Timeline/Events (placeholder)
   - Animated water flow diagram showing CHW and CDW loops

### Mock Features

All features are mocked for standalone frontend development:

- **realtime** (`src/features/realtime/index.ts`)
  - `useRealtime()` hook provides `getValue()`, `getUnit()`, `realtimeData`
  - Mock data includes: plant metrics, water loop temperatures/flows, equipment status

- **ontology** (`src/features/ontology/index.ts`)
  - `useOntologyEntities()` returns mock equipment entities
  - Equipment types: chiller, pchp, cdp, ct (cooling tower)

- **afdd** (`src/features/afdd/hooks.ts`)
  - `useAFDDAlertSummary()` returns alert categories

### Plant Diagram Animation

The `PlantDiagram.tsx` component shows animated water flow:
- Animation triggers when `flow_rate >= 1` in mock data
- Two loops: Chilled Water (CHW) and Condenser Water (CDW)
- Colors: CHR (light blue), CHS (dark blue), CDR (orange), CDS (yellow)

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

## Important Implementation Notes

### CSS Variables (globals.css)

The app uses CSS variables for theming. Key colors:
- `--primary`: #0d6de3 (blue)
- `--primary-dark`: #0654a7
- `--card-foreground`: #065BA9
- `--success`: #14b8b2 (teal)
- `--warning`: #fecb52 (yellow)
- `--danger`: #ef4134 (red)

### Equipment Status Values

In mock data, equipment status uses:
- `status_read: 0` = Standby (gray)
- `status_read: 1` = Running (blue border)
- `alarm: 1` = Alarm state (red)

### Component Origins

Most dashboard components were copied from `alto-cero-interface` project and adapted:
- Removed Supabase real-time subscriptions
- Replaced with mock data hooks
- Kept same visual styling and animations

## Future Development

### Planned Features
1. **Backend Integration**: Replace mock data with real API calls
2. **Air-Side Monitoring**: Add air handling unit dashboards
3. **ML Optimization**: Integrate machine learning recommendations
4. **Timeline/Events**: Right column for operational events
5. **Hotel Guest Rooms**: Room-level HVAC monitoring

### Backend Requirements
When implementing backend:
- Real-time WebSocket for live data
- Ontology API for equipment queries
- Timeseries API for historical data
- AFDD API for alerts

## Related Projects

- `alto-cero-interface`: Original project where components were copied from
- Components reference the same styling patterns and CSS classes

## Troubleshooting

### Common Issues

1. **Animation not working**: Check that `flow_rate` values in `src/features/realtime/index.ts` are >= 1

2. **Layout spacing issues**: Check `globals.css` body styles - should NOT have `display: flex; justify-content: center`

3. **Missing dependencies**: Run `npm install` - key deps include:
   - `@radix-ui/react-slot` (for button component)
   - `react-icons` (for icons)
   - `luxon` (for date formatting)
