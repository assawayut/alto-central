import React from 'react'
import { useParams } from 'react-router-dom'
import { PageLayout } from '@/components/layout/PageLayout'
import EnergyUsageCard from './components/EnergyUsageCard'
import BuildingLoadGraph from './components/BuildingLoadGraph'
import SystemAlertCard from './components/SystemAlertCard'
import EfficiencyCard from './components/EfficiencyCard'
import PowerCard from './components/PowerCard'
import WeatherStationCard from './components/WeatherStationCard'
import PlantEquipmentCard from './components/PlantEquipmentCard'
import PlantDiagram from './components/PlantDiagram'
import UpcomingEventsCard from './components/UpcomingEventsCard'
import { getSiteById, sites } from '@/config/sites'

export function ChillerPlant() {
  const { siteId } = useParams<{ siteId: string }>()

  // Find site info from config
  const site = getSiteById(siteId || '') || sites[0]

  return (
    <PageLayout
      title={site.site_name}
      subtitle="Chiller Plant"
      showBack
      backTo="/"
    >
      {/* Tab Navigation */}
      <div className="mb-4">
        <div className="inline-flex bg-white rounded-lg p-1 border border-border">
          <button className="px-4 py-2 text-sm font-medium bg-primary text-white rounded-md">
            Water-Side
          </button>
          <button className="px-4 py-2 text-sm font-medium text-muted hover:text-foreground rounded-md">
            Air-Side
          </button>
        </div>
      </div>

      {/* Main Layout: Left (20%) - Center (55%) - Right (25%) */}
      <div className="grid grid-cols-12 gap-4">
        {/* Left Column - 20% */}
        <div className="col-span-12 lg:col-span-3 xl:col-span-2 space-y-4">
          <EnergyUsageCard />
          <BuildingLoadGraph />
          <SystemAlertCard />
        </div>

        {/* Center Column - 55% */}
        <div className="col-span-12 lg:col-span-6 xl:col-span-7 space-y-4">
          {/* Top Row: Efficiency, Power (with Cooling Load & Part-Load), Weather */}
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

          {/* Bottom Row: System Status (left) + Plant Diagram (right) */}
          <div className="grid grid-cols-12 gap-4">
            {/* Left Side: System Status */}
            <div className="col-span-12 lg:col-span-5">
              <PlantEquipmentCard />
            </div>

            {/* Right Side: Plant Diagram */}
            <div className="col-span-12 lg:col-span-7">
              <div className="alto-card p-4 h-full">
                <PlantDiagram variant="water-cooled" />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - 25% */}
        <div className="col-span-12 lg:col-span-3">
          <UpcomingEventsCard />
        </div>
      </div>
    </PageLayout>
  )
}
