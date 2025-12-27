import React from 'react'
import { useParams } from 'react-router-dom'
import { PageLayout } from '@/components/layout/PageLayout'
import BuildingLoadGraph from './components/BuildingLoadGraph'
import SystemAlertCard from './components/SystemAlertCard'
import EfficiencyCard from './components/EfficiencyCard'
import PowerCard from './components/PowerCard'
import WeatherStationCard from './components/WeatherStationCard'
import PlantEquipmentCard from './components/PlantEquipmentCard'
import PlantDiagram from './components/PlantDiagram'
import { mockSites } from '@/data/mockData'

export function ChillerPlant() {
  const { siteId } = useParams<{ siteId: string }>()

  // Find site info
  const site = mockSites.find(s => s.id === siteId) || mockSites[0]

  return (
    <PageLayout
      title={site.name}
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
          <BuildingLoadGraph />
          <SystemAlertCard />
        </div>

        {/* Center Column - 55% */}
        <div className="col-span-12 lg:col-span-6 xl:col-span-7 space-y-4">
          {/* Top Row: Efficiency, Power, Weather */}
          <div className="grid grid-cols-12 gap-4">
            <div className="col-span-12 md:col-span-5">
              <EfficiencyCard
                thresholds={[0.0, 0.6, 0.7, 0.8, 1.0]}
                deviceId="plant"
                title="Water-Side Efficiency"
              />
            </div>
            <div className="col-span-6 md:col-span-3">
              <PowerCard deviceId="plant" title="Water-Side Power" />
            </div>
            <div className="col-span-6 md:col-span-4">
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
          <div className="alto-card h-full min-h-[400px] flex items-center justify-center text-muted text-sm">
            <div className="text-center">
              <p className="font-medium text-primary-dark mb-2">Timeline / Events</p>
              <p className="text-xs">(Coming Soon)</p>
            </div>
          </div>
        </div>
      </div>
    </PageLayout>
  )
}
