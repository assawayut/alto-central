import type { Site } from '@/types/site'
import type { PlantData, BuildingLoadPoint, Equipment } from '@/types/equipment'

export const mockSites: Site[] = [
  {
    id: 'jwm-bangkok',
    name: 'JW Marriott Bangkok',
    location: { lat: 13.7440, lng: 100.5553 },
    address: '4 Sukhumvit Rd, Khlong Toei, Bangkok 10110',
    type: 'hotel',
    status: 'active',
    chillerCount: 4,
    efficiency: 0.68,
    power: 850,
    coolingLoad: 1250,
  },
  {
    id: 'sc-tower',
    name: 'SC Tower',
    location: { lat: 13.7315, lng: 100.5685 },
    address: '123 Silom Rd, Bang Rak, Bangkok 10500',
    type: 'office',
    status: 'active',
    chillerCount: 3,
    efficiency: 0.72,
    power: 620,
    coolingLoad: 860,
  },
  {
    id: 'central-world',
    name: 'Central World',
    location: { lat: 13.7466, lng: 100.5392 },
    address: '999 Rama I Rd, Pathum Wan, Bangkok 10330',
    type: 'mall',
    status: 'warning',
    chillerCount: 6,
    efficiency: 0.85,
    power: 2400,
    coolingLoad: 2800,
  },
  {
    id: 'bumrungrad',
    name: 'Bumrungrad Hospital',
    location: { lat: 13.7513, lng: 100.5587 },
    address: '33 Sukhumvit 3, Khlong Toei Nuea, Bangkok 10110',
    type: 'hospital',
    status: 'active',
    chillerCount: 5,
    efficiency: 0.65,
    power: 1800,
    coolingLoad: 2770,
  },
]

export const mockEquipment: Equipment[] = [
  // Chillers
  { id: 'ch-1', name: 'CH-1', type: 'chiller', status: 'standby', power: 0, coolingCapacity: 0 },
  { id: 'ch-2', name: 'CH-2', type: 'chiller', status: 'standby', power: 0, coolingCapacity: 0 },
  { id: 'ch-3', name: 'CH-3', type: 'chiller', status: 'standby', power: 0, coolingCapacity: 0 },
  { id: 'ch-4', name: 'CH-4', type: 'chiller', status: 'running', power: 76, coolingCapacity: 75 },

  // Primary Chilled Water Pumps
  { id: 'pchp-1', name: 'PCHP-1', type: 'pchp', status: 'standby' },
  { id: 'pchp-2', name: 'PCHP-2', type: 'pchp', status: 'standby' },
  { id: 'pchp-3', name: 'PCHP-3', type: 'pchp', status: 'standby' },
  { id: 'pchp-4', name: 'PCHP-4', type: 'pchp', status: 'running' },

  // Secondary Chilled Water Pumps (none in this example)

  // Condenser Water Pumps
  { id: 'cdp-1', name: 'CDP-1', type: 'cdp', status: 'standby' },
  { id: 'cdp-2', name: 'CDP-2', type: 'cdp', status: 'standby' },
  { id: 'cdp-3', name: 'CDP-3', type: 'cdp', status: 'standby' },
  { id: 'cdp-4', name: 'CDP-4', type: 'cdp', status: 'running' },

  // Cooling Towers
  { id: 'ct-1', name: 'CT-1', type: 'ct', status: 'standby' },
  { id: 'ct-2', name: 'CT-2', type: 'ct', status: 'standby' },
  { id: 'ct-3', name: 'CT-3', type: 'ct', status: 'running' },
  { id: 'ct-4', name: 'CT-4', type: 'ct', status: 'standby' },
  { id: 'ct-5', name: 'CT-5', type: 'ct', status: 'running' },
  { id: 'ct-6', name: 'CT-6', type: 'ct', status: 'standby' },
]

export const mockPlantData: PlantData = {
  siteId: 'jwm-bangkok',
  siteName: 'JW Marriott Bangkok',
  efficiency: 1.022,
  totalPower: 76,
  coolingLoad: 75,
  maxCapacity: 300,
  heatReject: 2,
  temperatures: {
    chs: 48.1,
    chr: 52.8,
    cds: 77.8,
    cdr: 84.5,
    setpoint: 48.0,
  },
  flowRates: {
    chw: 378,
    cdw: 7,
  },
  equipment: mockEquipment,
  weather: {
    dbt: 87.1,
    wbt: 73.5,
    humidity: 53.0,
  },
  systemStatus: {
    waterSide: 'normal',
    airSide: 'normal',
    others: 'normal',
  },
}

export const mockBuildingLoad: BuildingLoadPoint[] = [
  { hour: 0, coolingLoad: 45, power: 35 },
  { hour: 1, coolingLoad: 40, power: 32 },
  { hour: 2, coolingLoad: 38, power: 30 },
  { hour: 3, coolingLoad: 35, power: 28 },
  { hour: 4, coolingLoad: 35, power: 28 },
  { hour: 5, coolingLoad: 40, power: 32 },
  { hour: 6, coolingLoad: 55, power: 45 },
  { hour: 7, coolingLoad: 85, power: 70 },
  { hour: 8, coolingLoad: 120, power: 100 },
  { hour: 9, coolingLoad: 150, power: 125 },
  { hour: 10, coolingLoad: 175, power: 145 },
  { hour: 11, coolingLoad: 190, power: 158 },
  { hour: 12, coolingLoad: 200, power: 166 },
  { hour: 13, coolingLoad: 195, power: 162 },
  { hour: 14, coolingLoad: 185, power: 154 },
  { hour: 15, coolingLoad: 170, power: 142 },
  { hour: 16, coolingLoad: 150, power: 125 },
  { hour: 17, coolingLoad: 130, power: 108 },
  { hour: 18, coolingLoad: 100, power: 83 },
  { hour: 19, coolingLoad: 80, power: 67 },
  { hour: 20, coolingLoad: 70, power: 58 },
  { hour: 21, coolingLoad: 60, power: 50 },
  { hour: 22, coolingLoad: 55, power: 46 },
  { hour: 23, coolingLoad: 50, power: 42 },
]
