import React, { createContext, useContext } from 'react';

interface MaintenanceData {
  [deviceId: string]: {
    status: 'under_maintenance' | 'completed';
    ticket_started_at: string;
    ticket_closed_at: string | null;
    description: string;
    ticket_started_by: string;
    ticket_closed_by: string | null;
  };
}

interface DeviceData {
  [id: string]: {
    entityId: string;
    name: string;
    model: string;
  };
}

export interface Device {
  id: string;
  entityId: string;
  name: string;
  model: string;
}

interface DeviceContextType {
  maintenanceData: MaintenanceData;
  deviceData: DeviceData;
  isDeviceUnderMaintenance: (deviceId: string) => boolean;
  getDeviceMaintenanceInfo: (deviceId: string) => MaintenanceData[string] | null;
  getDeviceName: (deviceId: string) => string | null;
  getDevicesByType: () => Record<string, Device[]>;
}

const DeviceContext = createContext<DeviceContextType | undefined>(undefined);

// Mock data
const mockDeviceData: DeviceData = {
  'ch-1': { entityId: 'ch-1', name: 'Chiller 1', model: 'chiller' },
  'ch-2': { entityId: 'ch-2', name: 'Chiller 2', model: 'chiller' },
  'ch-3': { entityId: 'ch-3', name: 'Chiller 3', model: 'chiller' },
  'ch-4': { entityId: 'ch-4', name: 'Chiller 4', model: 'chiller' },
  'pchp-1': { entityId: 'pchp-1', name: 'PCHP 1', model: 'pchp' },
  'pchp-2': { entityId: 'pchp-2', name: 'PCHP 2', model: 'pchp' },
  'pchp-3': { entityId: 'pchp-3', name: 'PCHP 3', model: 'pchp' },
  'pchp-4': { entityId: 'pchp-4', name: 'PCHP 4', model: 'pchp' },
  'cdp-1': { entityId: 'cdp-1', name: 'CDP 1', model: 'cdp' },
  'cdp-2': { entityId: 'cdp-2', name: 'CDP 2', model: 'cdp' },
  'cdp-3': { entityId: 'cdp-3', name: 'CDP 3', model: 'cdp' },
  'cdp-4': { entityId: 'cdp-4', name: 'CDP 4', model: 'cdp' },
  'ct-1': { entityId: 'ct-1', name: 'CT 1', model: 'ct' },
  'ct-2': { entityId: 'ct-2', name: 'CT 2', model: 'ct' },
  'ct-3': { entityId: 'ct-3', name: 'CT 3', model: 'ct' },
  'ct-4': { entityId: 'ct-4', name: 'CT 4', model: 'ct' },
  'ct-5': { entityId: 'ct-5', name: 'CT 5', model: 'ct' },
  'ct-6': { entityId: 'ct-6', name: 'CT 6', model: 'ct' },
};

const mockMaintenanceData: MaintenanceData = {};

export function DeviceProvider({ children }: { children: React.ReactNode }) {
  const isDeviceUnderMaintenance = (entityId: string): boolean => {
    return !!mockMaintenanceData[entityId] && mockMaintenanceData[entityId].status === 'under_maintenance';
  };

  const getDeviceMaintenanceInfo = (entityId: string): MaintenanceData[string] | null => {
    return mockMaintenanceData[entityId] || null;
  };

  const getDeviceName = (entityId: string): string | null => {
    for (const id in mockDeviceData) {
      if (mockDeviceData[id].entityId === entityId) {
        return mockDeviceData[id].name;
      }
    }
    return null;
  };

  const getDevicesByType = (): Record<string, Device[]> => {
    const devicesByType: Record<string, Device[]> = {};
    for (const id in mockDeviceData) {
      const device = mockDeviceData[id];
      if (!devicesByType[device.model]) {
        devicesByType[device.model] = [];
      }
      devicesByType[device.model].push({
        id,
        entityId: device.entityId,
        name: device.name,
        model: device.model,
      });
    }
    return devicesByType;
  };

  return (
    <DeviceContext.Provider value={{
      maintenanceData: mockMaintenanceData,
      deviceData: mockDeviceData,
      isDeviceUnderMaintenance,
      getDeviceMaintenanceInfo,
      getDeviceName,
      getDevicesByType
    }}>
      {children}
    </DeviceContext.Provider>
  );
}

export function useDevice() {
  const context = useContext(DeviceContext);
  if (context === undefined) {
    throw new Error('useDevice must be used within a DeviceProvider');
  }
  return context;
}
