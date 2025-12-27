import React from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { useNavigate } from 'react-router-dom'
import L from 'leaflet'
import type { Site } from '@/types/site'

// Custom marker icons based on status
const createMarkerIcon = (status: Site['status']) => {
  const colors = {
    active: '#14B8B4',
    warning: '#FF9F1C',
    alarm: '#EF4337',
    offline: '#B4B4B4',
  }

  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        background-color: ${colors[status]};
        width: 32px;
        height: 32px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          transform: rotate(45deg);
          color: white;
          font-size: 14px;
        ">🏢</div>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  })
}

interface MapViewProps {
  sites: Site[]
}

export function MapView({ sites }: MapViewProps) {
  const navigate = useNavigate()

  // Center on Bangkok
  const center: [number, number] = [13.7440, 100.5500]

  return (
    <div className="h-[500px] rounded-lg overflow-hidden alto-card">
      <MapContainer
        center={center}
        zoom={13}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {sites.map((site) => (
          <Marker
            key={site.id}
            position={[site.location.lat, site.location.lng]}
            icon={createMarkerIcon(site.status)}
            eventHandlers={{
              click: () => navigate(`/site/${site.id}`),
            }}
          >
            <Popup>
              <div className="p-2 min-w-[200px]">
                <h3 className="font-semibold text-foreground mb-1">{site.name}</h3>
                <p className="text-xs text-muted mb-2">{site.address}</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-muted">Chillers:</span>{' '}
                    <span className="font-medium">{site.chillerCount}</span>
                  </div>
                  <div>
                    <span className="text-muted">Efficiency:</span>{' '}
                    <span className="font-medium">{site.efficiency.toFixed(2)} kW/RT</span>
                  </div>
                  <div>
                    <span className="text-muted">Power:</span>{' '}
                    <span className="font-medium">{site.power} kW</span>
                  </div>
                  <div>
                    <span className="text-muted">Load:</span>{' '}
                    <span className="font-medium">{site.coolingLoad} RT</span>
                  </div>
                </div>
                <button
                  onClick={() => navigate(`/site/${site.id}`)}
                  className="mt-3 w-full bg-primary text-white text-xs py-1.5 rounded-md hover:bg-primary-dark transition-colors"
                >
                  View Dashboard
                </button>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}
