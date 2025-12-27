export interface Site {
  id: string
  name: string
  location: {
    lat: number
    lng: number
  }
  address: string
  type: 'hotel' | 'office' | 'mall' | 'hospital' | 'industrial'
  status: 'active' | 'warning' | 'alarm' | 'offline'
  chillerCount: number
  efficiency: number // kW/RT
  power: number // kW
  coolingLoad: number // RT
}

export interface SiteOverview {
  totalSites: number
  activeSites: number
  totalPower: number
  avgEfficiency: number
}
