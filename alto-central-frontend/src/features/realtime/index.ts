import React, { createContext, useContext, ReactNode } from 'react'

// Mock data for demonstration
const mockRealtimeData: Record<string, Record<string, number | string>> = {
  plant: {
    power: 86,
    cooling_rate: 90,
    efficiency: 0.960,
    chs_temperature: 47.2,
    chr_temperature: 52.9,
    cds_temperature: 77.4,
    cdr_temperature: 84.6,
    chw_flow: 381,
    cdw_flow: 7,
    setpoint: 47.0,
    heat_reject: 2,
    building_load: 90,
    power_all_chillers: 76,
    power_all_pchps: 12,
    power_all_cdps: 8,
    power_all_cts: 5,
  },
  // Water loop data for PlantDiagram animation
  chilled_water_loop: {
    return_water_temperature: 52.9,
    supply_water_temperature: 47.2,
    flow_rate: 381,
  },
  condenser_water_loop: {
    return_water_temperature: 84.6,
    supply_water_temperature: 77.4,
    flow_rate: 7,
  },
  air_distribution_system: {
    power: 45,
  },
  outdoor_weather_station: {
    drybulb_temperature: 86.4,
    wetbulb_temperature: 73.3,
    humidity: 54.1,
  },
  // Equipment status
  'ch-1': { status_read: 0, alarm: 0 },
  'ch-2': { status_read: 0, alarm: 0 },
  'ch-3': { status_read: 0, alarm: 0 },
  'ch-4': { status_read: 1, alarm: 0 },
  'pchp-1': { status_read: 0, alarm: 0 },
  'pchp-2': { status_read: 0, alarm: 0 },
  'pchp-3': { status_read: 0, alarm: 0 },
  'pchp-4': { status_read: 1, alarm: 0 },
  'cdp-1': { status_read: 0, alarm: 0 },
  'cdp-2': { status_read: 0, alarm: 0 },
  'cdp-3': { status_read: 0, alarm: 0 },
  'cdp-4': { status_read: 1, alarm: 0 },
  'ct-1': { status_read: 0, alarm: 0 },
  'ct-2': { status_read: 0, alarm: 0 },
  'ct-3': { status_read: 1, alarm: 0 },
  'ct-4': { status_read: 0, alarm: 0 },
  'ct-5': { status_read: 1, alarm: 0 },
  'ct-6': { status_read: 0, alarm: 0 },
}

// Unit mapping
const unitMap: Record<string, Record<string, string>> = {
  outdoor_weather_station: {
    drybulb_temperature: '°F',
    wetbulb_temperature: '°F',
    humidity: '%',
  },
  plant: {
    chs_temperature: '°F',
    chr_temperature: '°F',
    cds_temperature: '°F',
    cdr_temperature: '°F',
    chw_flow: 'GPM',
    cdw_flow: 'GPM',
    power: 'kW',
    cooling_rate: 'RT',
  },
  chilled_water_loop: {
    return_water_temperature: '°F',
    supply_water_temperature: '°F',
    flow_rate: 'GPM',
  },
  condenser_water_loop: {
    return_water_temperature: '°F',
    supply_water_temperature: '°F',
    flow_rate: 'GPM',
  },
  '': {
    setpoint_read: '°F',
  },
}

interface RealtimeContextType {
  getValue: (deviceId: string, datapoint: string) => number | string | undefined
  getRawValue: (deviceId: string, datapoint: string) => number | string | undefined
  getUnit: (deviceId: string, datapoint: string) => string
}

const RealtimeContext = createContext<RealtimeContextType | null>(null)

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const getValue = (deviceId: string, datapoint: string) => {
    return mockRealtimeData[deviceId]?.[datapoint]
  }

  const getRawValue = (deviceId: string, datapoint: string) => {
    return mockRealtimeData[deviceId]?.[datapoint]
  }

  const getUnit = (deviceId: string, datapoint: string) => {
    return unitMap[deviceId]?.[datapoint] || ''
  }

  return React.createElement(
    RealtimeContext.Provider,
    { value: { getValue, getRawValue, getUnit } },
    children
  )
}

export function useRealtime() {
  const context = useContext(RealtimeContext)
  if (!context) {
    // Return mock functions if not in provider
    return {
      realtimeData: mockRealtimeData,
      getValue: (deviceId: string, datapoint: string) => mockRealtimeData[deviceId]?.[datapoint],
      getRawValue: (deviceId: string, datapoint: string) => mockRealtimeData[deviceId]?.[datapoint],
      getUnit: (deviceId: string, datapoint: string) => unitMap[deviceId]?.[datapoint] || '',
    }
  }
  return { ...context, realtimeData: mockRealtimeData }
}
