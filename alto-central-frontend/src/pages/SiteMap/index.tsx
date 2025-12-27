import React from 'react'
import { Building2, Zap, Activity, MapPin } from 'lucide-react'
import { PageLayout } from '@/components/layout/PageLayout'
import { Card } from '@/components/ui/card'
import { MapView } from './components/MapView'
import { BuildingCard } from './components/BuildingCard'
import { mockSites } from '@/data/mockData'

export function SiteMap() {
  // Calculate overview stats
  const overview = {
    totalSites: mockSites.length,
    activeSites: mockSites.filter(s => s.status === 'active').length,
    totalPower: mockSites.reduce((sum, s) => sum + s.power, 0),
    avgEfficiency: mockSites.reduce((sum, s) => sum + s.efficiency, 0) / mockSites.length,
  }

  return (
    <PageLayout title="ALTO HVAC Central" subtitle="Centralized HVAC Operation System">
      {/* Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#E5F2FF] rounded-lg">
              <MapPin className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{overview.totalSites}</p>
              <p className="text-xs text-muted">Total Sites</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#CBF0EF] rounded-lg">
              <Building2 className="h-5 w-5 text-[#14B8B4]" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{overview.activeSites}</p>
              <p className="text-xs text-muted">Active Sites</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#FFF5E5] rounded-lg">
              <Zap className="h-5 w-5 text-[#FF9F1C]" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{overview.totalPower.toLocaleString()}</p>
              <p className="text-xs text-muted">Total Power (kW)</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#E5F2FF] rounded-lg">
              <Activity className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{overview.avgEfficiency.toFixed(2)}</p>
              <p className="text-xs text-muted">Avg Efficiency (kW/RT)</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Map */}
      <div className="mb-6">
        <MapView sites={mockSites} />
      </div>

      {/* Site Cards */}
      <div>
        <h2 className="text-lg font-semibold text-foreground mb-4">All Sites</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {mockSites.map((site) => (
            <BuildingCard key={site.id} site={site} />
          ))}
        </div>
      </div>
    </PageLayout>
  )
}
