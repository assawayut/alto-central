import React, { useState, useMemo, useEffect } from 'react';
import { useRealtime } from '@/features/realtime';
import { useDevice } from '@/contexts/DeviceContext';
import { cn } from '@/utils/cn';
import { OntologyEntity } from '@/features/ontology';
import { useOntologyEntities } from '@/features/ontology';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

// Water-side entity interface
interface WaterSideEntity extends OntologyEntity {
  equipmentType: string;
  status: 'normal' | 'off' | 'warning' | 'alarm';
}

interface StatusIndicatorProps {
  status: 'running' | 'standby' | 'alarm' | 'under_maintenance';
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status }) => {
  const getStatusStyles = () => {
    switch (status) {
      case 'running':
        return {
          bg: 'bg-[#14B8B4]',
          border: 'border-[#14B8B4]',
          bgWithOpacity: 'bg-[#14B8B4]/20',
          fontColor: 'text-[#14B8B4]'
        };
      case 'alarm':
        return {
          bg: 'bg-[#F43F5E]',
          border: 'border-[#F43F5E]',
          bgWithOpacity: 'bg-[#F43F5E]/20',
          fontColor: 'text-[#F43F5E]'
        };
      case 'under_maintenance':
        return {
          bg: 'bg-[#F9C36A]',
          border: 'border-[#F9C36A]',
          bgWithOpacity: 'bg-[#F9C36A]/20',
          fontColor: 'text-[#F9C36A]'
        };
      case 'standby':
      default:
        return {
          bg: 'bg-[#B4B4B4]',
          border: 'border-[#B4B4B4]',
          bgWithOpacity: 'bg-[#B4B4B4]/20',
          fontColor: 'text-[#B4B4B4]'
        };
    }
  };

  const getStatusText = () => {
    if (status === 'under_maintenance') return 'Maintenance';
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  const styles = getStatusStyles();

  return (
    <div className={cn(
      "flex justify-center items-center flex-row gap-2 rounded-[15px] px-2 h-[18px] my-auto",
      styles.bgWithOpacity,
      styles.border
    )}>
      <div className={cn(styles.bg, "rounded-[100px] w-[6px] h-[6px]")}></div>
      <span className={cn(styles.fontColor, "text-[9px]")}>{getStatusText()}</span>
    </div>
  );
};

interface EquipmentSectionProps {
  title: string;
  efficiency: number;
  model: string;
  devices: any[];
}

const EquipmentSection: React.FC<EquipmentSectionProps> = ({ title, efficiency, model, devices }) => {
  const { getValue } = useRealtime();
  const { isDeviceUnderMaintenance } = useDevice();

  const getDeviceStatus = (entityId: string): StatusIndicatorProps['status'] => {
    if (isDeviceUnderMaintenance(entityId)) {
      return 'under_maintenance';
    }
    
    const alarm = getValue(entityId, 'alarm');
    if (alarm) {
      return 'alarm';
    }

    const statusRead = getValue(entityId, 'status_read');
    return (statusRead === 1) ? 'running' : 'standby';
  };

  return (
    <div className="flex self-stretch justify-start items-start flex-col gap-1.5 pt-1">
      <div className="flex self-stretch justify-between items-center flex-row gap-1.5">
        <span className="text-[#065BA9] text-xs text-center font-semibold">{title}</span>
        <div className="flex justify-start items-center flex-row gap-1.5">
          <span className="text-[#065BA9] text-xs text-center font-semibold">{efficiency.toFixed(3)}</span>
          <span className="text-[#6B7280] text-[9px] text-center">kW/Ton</span>
        </div>
      </div>
      
      <div className="w-full rounded-md overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-[#EDEFF9] border-[#DBE4FF]">
              {model === 'chiller' ? (
                <>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">Device Name</TableHead>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">Status</TableHead>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">Power (kW)</TableHead>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">Efficiency</TableHead>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">Setpoint(°F)</TableHead>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">CHS (°F)</TableHead>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">CHR (°F)</TableHead>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">CDR (°F)</TableHead>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">CDS (°F)</TableHead>
                </>
              ) : (
                <>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">Device Name</TableHead>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">Status</TableHead>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">Power (kW)</TableHead>
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">Frequency (Hz)</TableHead>
                </>
              )}
            </TableRow>
          </TableHeader>
          <TableBody>
            {devices.map((device) => {
              const status = getDeviceStatus(device.entity_id);
              
              if (model === 'chiller') {
                const power = getValue(device.entity_id, 'power');
                const deviceEfficiency = getValue(device.entity_id, 'efficiency');
                const setpoint = getValue(device.entity_id, 'setpoint_read');
                const chs = getValue(device.entity_id, 'evap_leaving_water_temperature');
                const chr = getValue(device.entity_id, 'evap_entering_water_temperature');
                const cdr = getValue(device.entity_id, 'cond_entering_water_temperature');
                const cds = getValue(device.entity_id, 'cond_leaving_water_temperature');
                
                return (
                  <TableRow key={device.entity_id} className="bg-[#F9FAFF] border-[#EDEFF9]">
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{device.entity_id.replace('chiller_', 'CH-')}</TableCell>
                    <TableCell className="h-[32px] py-1 px-2 text-left flex justify-start"><StatusIndicator status={status} /></TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{power === undefined ? "-" : power.toFixed(1)}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{deviceEfficiency === undefined ? "-" : deviceEfficiency.toFixed(3)}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{setpoint === undefined ? "-" : `${setpoint.toFixed(1)}`}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{chs === undefined ? "-" : `${chs.toFixed(1)}`}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{chr === undefined ? "-" : `${chr.toFixed(1)}`}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{cdr === undefined ? "-" : `${cdr.toFixed(1)}`}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{cds === undefined ? "-" : `${cds.toFixed(1)}`}</TableCell>
                  </TableRow>
                );
              } else {
                const power = getValue(device.entity_id, 'power') || 0;
                const frequency = getValue(device.entity_id, 'frequency_read') || 0;
                
                return (
                  <TableRow key={device.entity_id} className="bg-[#F9FAFF] border-[#EDEFF9]">
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{device.entity_id.replace(/_/g, '-').toUpperCase()}</TableCell>
                    <TableCell className="h-[32px] py-1 px-2 text-left flex justify-start"><StatusIndicator status={status} /></TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{power === undefined ? "-" : power.toFixed(1)}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{frequency === undefined ? "-" : frequency.toFixed(1)}</TableCell>
                  </TableRow>
                );
              }
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

interface PlantEquipmentModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Utility functions moved outside component to avoid hoisting issues
const getEquipmentType = (tags?: Record<string, any>): string => {
  if (!tags) return 'unknown';
  if (tags.model === 'chiller') return 'chiller';
  if (tags.model === 'pchp') return 'pchp';
  if (tags.model === 'schp') return 'pchp';
  if (tags.model === 'cdp') return 'cdp';
  if (tags.model === 'ct') return 'ct';
  return 'unknown';
};

const getEquipmentStatus = (entity: OntologyEntity): 'normal' | 'off' | 'warning' | 'alarm' => {
  const statusData = entity.latest_data?.status_read;
  if (!statusData || statusData.is_stale) {
    return 'off';
  }

  const statusValue = Number(statusData.value);
  const alarmData = entity.latest_data?.alarm;
  
  if (alarmData && Number(alarmData.value) === 1) {
    return 'alarm';
  }
  
  if (statusValue === 1) {
    return 'normal';
  }
  
  return 'off';
};

const PlantEquipmentModal: React.FC<PlantEquipmentModalProps> = ({ isOpen, onClose }) => {
  const { getValue } = useRealtime();
  const [isVisible, setIsVisible] = useState(false);
  const [shouldRender, setShouldRender] = useState(isOpen);

  // Fetch water-side equipment using ontology hook
  const { entities: waterEntities, loading: isLoading } = useOntologyEntities({
    tag_filter: 'spaceRef:plant',
    expand: ['tags', 'latest_data']
  });
  
  // Convert water entities to WaterSideEntity format
  const waterEquipment = useMemo(() => {
    return waterEntities.map((entity): WaterSideEntity => ({
      ...entity,
      equipmentType: getEquipmentType(entity.tags),
      status: getEquipmentStatus(entity)
    }));
  }, [waterEntities]);


  // Group equipment by type
  const devicesByType = {
    'chiller': waterEquipment.filter(e => e.equipmentType === 'chiller'),
    'pchp': waterEquipment.filter(e => e.equipmentType === 'pchp'),
    'cdp': waterEquipment.filter(e => e.equipmentType === 'cdp'),
    'ct': waterEquipment.filter(e => e.equipmentType === 'ct')
  };
  
  // Get plant cooling rate for efficiency calculations
  const coolingRate = getValue('plant', 'cooling_rate');
  
  // Calculate efficiencies using plant-level aggregated power values
  const powerAllChillers = getValue('plant', 'power_all_chillers');
  const powerAllPCHPs = getValue('plant', 'power_all_pchps');
  const powerAllCDPs = getValue('plant', 'power_all_cdps');
  const powerAllCTs = getValue('plant', 'power_all_cts');

  const plantEfficiency = coolingRate > 0 && powerAllChillers != null ? powerAllChillers / coolingRate : 0;
  const pchpEfficiency = coolingRate > 0 && powerAllPCHPs != null ? powerAllPCHPs / coolingRate : 0;
  const cdpEfficiency = coolingRate > 0 && powerAllCDPs != null ? powerAllCDPs / coolingRate : 0;
  const coolingTowerEfficiency = coolingRate > 0 && powerAllCTs != null ? powerAllCTs / coolingRate : 0;

  // Handle opening and closing animations
  useEffect(() => {
    if (isOpen) {
      setShouldRender(true);
      const openTimer = setTimeout(() => {
        setIsVisible(true);
      }, 10);
      
      return () => clearTimeout(openTimer);
    } else {
      setIsVisible(false);
      const closeTimer = setTimeout(() => {
        setShouldRender(false);
      }, 300);
      
      return () => clearTimeout(closeTimer);
    }
  }, [isOpen]);

  if (!shouldRender) return null;

  return (
    <>
      {/* Background Overlay */}
      <div 
        className={cn(
          "fixed inset-0 bg-black transition-opacity duration-300 ease-in-out z-[998]",
          isVisible ? "opacity-50" : "opacity-0 pointer-events-none"
        )}
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div 
        className={cn(
          "fixed inset-0 flex items-center justify-center z-[999] p-4 overflow-auto transition-all duration-300 ease-in-out",
          !isVisible && "pointer-events-none"
        )}
        onClick={onClose}
      >
        <div 
          className={cn(
            "flex justify-start items-center flex-col gap-3 p-4 bg-[#F9FAFF] border-solid border-[#DBE4FF] border rounded-xl max-w-5xl w-full max-h-[90vh] overflow-auto transition-all duration-300 ease-in-out",
            isVisible ? "opacity-100 scale-100" : "opacity-0 scale-95 transform"
          )}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex self-stretch justify-between items-center flex-row gap-4">
            <div className="flex self-stretch justify-start items-center flex-row gap-2">
              <span className="text-[#065BA9] text-lg font-semibold">Water Side: System Status</span>
            </div>
            <button onClick={onClose} className="focus:outline-none">
              <svg width="24" height="25" viewBox="0 0 24 25" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M5.25 5.75L18.75 19.25M18.75 5.75L5.25 19.25" stroke="#0E7EE4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="flex self-stretch justify-start items-start flex-col gap-2 w-full">
            <EquipmentSection 
              title="Chiller" 
              efficiency={plantEfficiency}
              model="chiller"
              devices={devicesByType['chiller'] || []}
            />
            
            <EquipmentSection 
              title="PCHP" 
              efficiency={pchpEfficiency}
              model="pchp"
              devices={devicesByType['pchp'] || []}
            />
            
            <EquipmentSection 
              title="CDP" 
              efficiency={cdpEfficiency}
              model="cdp"
              devices={devicesByType['cdp'] || []}
            />
            
            <EquipmentSection 
              title="Cooling Tower" 
              efficiency={coolingTowerEfficiency}
              model="ct"
              devices={devicesByType['ct'] || []}
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default PlantEquipmentModal; 