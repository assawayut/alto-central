import React from 'react'
import { useParams } from 'react-router-dom'
import { PageLayout } from '@/components/layout/PageLayout'
import { RealtimeProvider } from '@/features/realtime'
import EnergyUsageCard from './components/EnergyUsageCard'
import BuildingLoadGraph from './components/BuildingLoadGraph'
import SystemAlertCard from './components/SystemAlertCard'
import EfficiencyCard from './components/EfficiencyCard'
import PowerCard from './components/PowerCard'
import WeatherStationCard from './components/WeatherStationCard'
import PlantEquipmentCard from './components/PlantEquipmentCard'
import PlantDiagram from './components/PlantDiagram'
import UpcomingEventsCard from './components/UpcomingEventsCard'
import DataAnalyticsCard from './components/DataAnalyticsCard'
import OptimizationCard from './components/OptimizationCard'
import { getSiteById, sites } from '@/config/sites'

function ChillerPlantContent() {
  const { siteId } = useParams<{ siteId: string }>()

  // Find site info from config
  const site = getSiteById(siteId || '') || sites[0]
  const showAirSideTab = site?.hvac_type !== 'water'

  return (
    <PageLayout
      title={site.site_name}
      subtitle="Chiller Plant"
      showBack
      backTo="/"
    >
      {/* Tab Navigation + Upcoming Events */}
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="inline-flex bg-white rounded-lg p-1 border border-border flex-shrink-0">
          <button className="px-4 py-2 text-sm font-medium bg-primary text-white rounded-md">
            Water-Side
          </button>
          {showAirSideTab && (
            <button className="px-4 py-2 text-sm font-medium text-muted hover:text-foreground rounded-md">
              Air-Side
            </button>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <UpcomingEventsCard />
        </div>
      </div>

      {/* Main Layout: Left - Center - Right */}
      <div className="grid grid-cols-12 gap-4">
        {/* Left Column */}
        <div className="col-span-12 lg:col-span-2 space-y-4">
          <EnergyUsageCard />
          <BuildingLoadGraph />
          <SystemAlertCard />
        </div>

        {/* Center Column */}
        <div className="col-span-12 lg:col-span-7 space-y-4">
          {/* Top Row: Efficiency, Power, Weather */}
          <div className="grid grid-cols-12 gap-4">
            <div className="col-span-12 md:col-span-4">
              <EfficiencyCard
                thresholds={[0.0, 0.6, 0.7, 0.8, 1.0]}
                deviceId="plant"
                title="Water-Side Efficiency"
              />
            </div>
            <div className="col-span-12 md:col-span-5">
              <PowerCard deviceId="plant" />
            </div>
            <div className="col-span-12 md:col-span-3">
              <WeatherStationCard />
            </div>
          </div>

          {/* Bottom Row: System Status + Plant Diagram (compact) */}
          <div className="grid grid-cols-12 gap-4">
            <div className="col-span-12 lg:col-span-6">
              <PlantEquipmentCard />
            </div>
            <div className="col-span-12 lg:col-span-6">
              <div className="alto-card p-2 h-full">
                <PlantDiagram variant="water-cooled" />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Analytics & Optimization */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          <DataAnalyticsCard />
          <OptimizationCard />
        </div>
      </div>
    </PageLayout>
  )
}

export function ChillerPlant() {
  return (
    <RealtimeProvider>
      <ChillerPlantContent />
    </RealtimeProvider>
  )
}
