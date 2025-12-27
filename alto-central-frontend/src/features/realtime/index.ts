import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { useParams } from 'react-router-dom'
import { API_ENDPOINTS, POLLING_INTERVAL } from '@/config/api'

// Types for API response
interface DatapointValue {
  value: number | string;
  updated_at?: string;
}

interface DevicesData {
  [deviceId: string]: {
    [datapoint: string]: DatapointValue;
  };
}

interface RealtimeResponse {
  site_id: string;
  timestamp: string;
  devices: DevicesData;
}

// Unit mapping for display
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
    efficiency: 'kW/RT',
    power_kw: 'kW',
    cooling_rate_rt: 'RT',
    efficiency_kw_rt: 'kW/RT',
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
    power: 'kW',
    frequency_read: 'Hz',
  },
}

interface RealtimeContextType {
  devices: DevicesData;
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;
  getValue: (deviceId: string, datapoint: string) => number | string | undefined;
  getRawValue: (deviceId: string, datapoint: string) => number | string | undefined;
  getUnit: (deviceId: string, datapoint: string) => string;
  getUpdatedAt: (deviceId: string, datapoint: string) => string | null;
  refetch: () => Promise<void>;
}

const RealtimeContext = createContext<RealtimeContextType | null>(null)

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const { siteId } = useParams<{ siteId: string }>()
  const [devices, setDevices] = useState<DevicesData>({})
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    if (!siteId) return

    try {
      const response = await fetch(API_ENDPOINTS.realtimeLatest(siteId))

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data: RealtimeResponse = await response.json()
      setDevices(data.devices || {})
      setLastUpdated(data.timestamp)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch realtime data:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setIsLoading(false)
    }
  }, [siteId])

  // Initial fetch and polling
  useEffect(() => {
    if (!siteId) return

    setIsLoading(true)
    fetchData()

    const interval = setInterval(fetchData, POLLING_INTERVAL)
    return () => clearInterval(interval)
  }, [siteId, fetchData])

  const getValue = useCallback((deviceId: string, datapoint: string): number | string | undefined => {
    const deviceData = devices[deviceId]
    if (!deviceData) return undefined

    const datapointData = deviceData[datapoint]
    if (!datapointData) return undefined

    return datapointData.value
  }, [devices])

  const getRawValue = useCallback((deviceId: string, datapoint: string): number | string | undefined => {
    return getValue(deviceId, datapoint)
  }, [getValue])

  const getUnit = useCallback((deviceId: string, datapoint: string): string => {
    // Check device-specific unit first
    if (unitMap[deviceId]?.[datapoint]) {
      return unitMap[deviceId][datapoint]
    }
    // Check generic unit
    if (unitMap['']?.[datapoint]) {
      return unitMap[''][datapoint]
    }
    return ''
  }, [])

  const getUpdatedAt = useCallback((deviceId: string, datapoint: string): string | null => {
    return devices[deviceId]?.[datapoint]?.updated_at ?? null
  }, [devices])

  const value: RealtimeContextType = {
    devices,
    isLoading,
    error,
    lastUpdated,
    getValue,
    getRawValue,
    getUnit,
    getUpdatedAt,
    refetch: fetchData,
  }

  return React.createElement(
    RealtimeContext.Provider,
    { value },
    children
  )
}

export function useRealtime() {
  const context = useContext(RealtimeContext)

  if (!context) {
    // Return empty functions if not in provider (for standalone usage)
    return {
      devices: {} as DevicesData,
      realtimeData: {} as DevicesData, // Backward compatibility alias
      isLoading: false,
      error: null,
      lastUpdated: null,
      getValue: (_deviceId: string, _datapoint: string) => undefined,
      getRawValue: (_deviceId: string, _datapoint: string) => undefined,
      getUnit: (deviceId: string, datapoint: string) => unitMap[deviceId]?.[datapoint] || unitMap['']?.[datapoint] || '',
      getUpdatedAt: (_deviceId: string, _datapoint: string) => null,
      refetch: async () => {},
    }
  }

  return {
    ...context,
    realtimeData: context.devices, // Backward compatibility alias
  }
}
