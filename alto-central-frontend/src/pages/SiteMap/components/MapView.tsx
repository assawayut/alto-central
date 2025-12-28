import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useNavigate } from 'react-router-dom';
import { sites, defaultMapCenter, SiteConfig } from '@/config/sites';

// OpenStreetMap-based style (free, no API key required)
const MAP_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
  },
  layers: [
    {
      id: 'osm',
      type: 'raster',
      source: 'osm',
      minzoom: 0,
      maxzoom: 19,
    },
  ],
};

// Create a custom marker element
const createMarkerElement = (site: SiteConfig, onClick: () => void): HTMLElement => {
  const container = document.createElement('div');
  container.className = 'site-marker-container';
  container.style.cssText = `
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    transform: translate(-50%, -100%);
  `;

  // Card/Block
  const card = document.createElement('div');
  card.className = 'site-marker-card';
  card.style.cssText = `
    background: white;
    border-radius: 8px;
    padding: 8px 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    min-width: 80px;
    text-align: center;
    transition: all 0.2s ease;
  `;

  // Site code (main label)
  const codeLabel = document.createElement('div');
  codeLabel.style.cssText = `
    font-size: 14px;
    font-weight: 600;
    color: #272E3B;
  `;
  codeLabel.textContent = site.site_code;

  card.appendChild(codeLabel);

  // Pin/Dot
  const pin = document.createElement('div');
  pin.style.cssText = `
    width: 8px;
    height: 8px;
    background: #F97316;
    border-radius: 50%;
    margin-top: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  `;

  // Pin line
  const line = document.createElement('div');
  line.style.cssText = `
    width: 2px;
    height: 20px;
    background: #F97316;
  `;

  container.appendChild(card);
  container.appendChild(line);
  container.appendChild(pin);

  // Hover effect
  container.addEventListener('mouseenter', () => {
    card.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
    card.style.transform = 'scale(1.05)';
  });
  container.addEventListener('mouseleave', () => {
    card.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.15)';
    card.style.transform = 'scale(1)';
  });

  // Click handler
  container.addEventListener('click', onClick);

  return container;
};

const MapView: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const navigate = useNavigate();
  const [mapLoaded, setMapLoaded] = useState(false);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Initialize map
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: MAP_STYLE,
      center: [defaultMapCenter.longitude, defaultMapCenter.latitude],
      zoom: defaultMapCenter.zoom,
    });

    // Add navigation controls
    map.current.addControl(
      new maplibregl.NavigationControl({
        visualizePitch: true,
      }),
      'top-right'
    );

    // Add fullscreen control
    map.current.addControl(
      new maplibregl.FullscreenControl(),
      'top-right'
    );

    map.current.on('load', () => {
      setMapLoaded(true);
    });

    return () => {
      // Cleanup markers
      markersRef.current.forEach(marker => marker.remove());
      markersRef.current = [];

      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Add markers when map is loaded
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Add markers for each site
    sites.forEach(site => {
      const markerElement = createMarkerElement(site, () => {
        navigate(`/site/${site.site_id}`);
      });

      const marker = new maplibregl.Marker({
        element: markerElement,
        anchor: 'bottom',
      })
        .setLngLat([site.longitude, site.latitude])
        .addTo(map.current!);

      markersRef.current.push(marker);
    });

    // Fit bounds to show all markers
    if (sites.length > 1) {
      const bounds = new maplibregl.LngLatBounds();
      sites.forEach(site => {
        bounds.extend([site.longitude, site.latitude]);
      });
      map.current.fitBounds(bounds, {
        padding: 80,
        maxZoom: 10,
      });
    }
  }, [mapLoaded, navigate]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full rounded-lg overflow-hidden" />

      {/* Loading overlay */}
      {!mapLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-sm text-gray-500">Loading map...</p>
          </div>
        </div>
      )}

      {/* Attribution styling */}
      <style>{`
        .maplibregl-ctrl-attrib {
          font-size: 10px;
          background: rgba(255, 255, 255, 0.8) !important;
        }
        .maplibregl-ctrl-group {
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        .maplibregl-ctrl-group button {
          width: 32px;
          height: 32px;
        }
      `}</style>
    </div>
  );
};

export default MapView;
