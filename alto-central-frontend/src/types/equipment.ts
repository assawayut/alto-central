export type EquipmentType = 'chiller' | 'pchp' | 'schp' | 'cdp' | 'ct'
export type EquipmentStatus = 'running' | 'standby' | 'maintenance' | 'alarm'

export interface Equipment {
  id: string
  name: string
  type: EquipmentType
  status: EquipmentStatus
  power?: number // kW
  coolingCapacity?: number // RT
  efficiency?: number // kW/RT
}

export interface EquipmentGroup {
  type: EquipmentType
  label: string
  fullName: string
  items: Equipment[]
}

export interface PlantData {
  siteId: string
  siteName: string
  efficiency: number // kW/RT
  totalPower: number // kW
  coolingLoad: number // RT
  maxCapacity: number // RT
  heatReject: number // Ton
  temperatures: {
    chs: number // Chilled Supply
    chr: number // Chilled Return
    cds: number // Condenser Supply
    cdr: number // Condenser Return
    setpoint: number // Chiller Plant Setpoint
  }
  flowRates: {
    chw: number // Chilled Water GPM
    cdw: number // Condenser Water GPM
  }
  equipment: Equipment[]
  weather: {
    dbt: number // Dry Bulb Temperature
    wbt: number // Wet Bulb Temperature
    humidity: number // %
  }
  systemStatus: {
    waterSide: 'normal' | 'warning' | 'alarm'
    airSide: 'normal' | 'warning' | 'alarm'
    others: 'normal' | 'warning' | 'alarm'
  }
}

export interface BuildingLoadPoint {
  hour: number
  coolingLoad: number // RT
  power: number // kW
}
