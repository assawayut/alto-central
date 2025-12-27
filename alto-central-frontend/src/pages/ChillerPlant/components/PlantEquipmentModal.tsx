import React, { useState, useMemo, useEffect } from 'react';
import { useRealtime } from '@/features/realtime';
import { useDevice } from '@/contexts/DeviceContext';
import { cn } from '@/utils/cn';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

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

interface EquipmentDevice {
  deviceId: string;
  number: string;
}

interface EquipmentSectionProps {
  title: string;
  efficiency: number;
  model: string;
  devices: EquipmentDevice[];
}

const EquipmentSection: React.FC<EquipmentSectionProps> = ({ title, efficiency, model, devices }) => {
  const { getValue } = useRealtime();
  const { isDeviceUnderMaintenance } = useDevice();

  const getDeviceStatus = (deviceId: string): StatusIndicatorProps['status'] => {
    if (isDeviceUnderMaintenance(deviceId)) {
      return 'under_maintenance';
    }

    const alarm = getValue(deviceId, 'alarm');
    if (alarm === 1) {
      return 'alarm';
    }

    const statusRead = getValue(deviceId, 'status_read');
    return (statusRead === 1) ? 'running' : 'standby';
  };

  const formatValue = (value: number | string | undefined): string => {
    if (value === undefined || value === null) return '-';
    if (typeof value === 'number') return value.toFixed(1);
    return String(value);
  };

  if (devices.length === 0) return null;

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
                  <TableHead className="h-[32px] text-[#788796] text-[9px] font-normal py-1 px-2 text-left">RLA (%)</TableHead>
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
              const status = getDeviceStatus(device.deviceId);

              if (model === 'chiller') {
                const power = getValue(device.deviceId, 'power');
                const rla = getValue(device.deviceId, 'percentage_rla');
                const deviceEfficiency = getValue(device.deviceId, 'efficiency');
                const setpoint = getValue(device.deviceId, 'setpoint_read');
                const chs = getValue(device.deviceId, 'evap_leaving_water_temperature');
                const chr = getValue(device.deviceId, 'evap_entering_water_temperature');
                const cdr = getValue(device.deviceId, 'cond_entering_water_temperature');
                const cds = getValue(device.deviceId, 'cond_leaving_water_temperature');

                return (
                  <TableRow key={device.deviceId} className="bg-[#F9FAFF] border-[#EDEFF9]">
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">CH-{device.number}</TableCell>
                    <TableCell className="h-[32px] py-1 px-2 text-left flex justify-start"><StatusIndicator status={status} /></TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{formatValue(power as number)}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{formatValue(rla as number)}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{deviceEfficiency !== undefined ? (deviceEfficiency as number).toFixed(3) : '-'}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{formatValue(setpoint as number)}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{formatValue(chs as number)}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{formatValue(chr as number)}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{formatValue(cdr as number)}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{formatValue(cds as number)}</TableCell>
                  </TableRow>
                );
              } else {
                const power = getValue(device.deviceId, 'power');
                const frequency = getValue(device.deviceId, 'frequency_read');

                // Format display name based on equipment type
                let displayName = device.deviceId.replace(/_/g, '-').toUpperCase();
                if (model === 'pchp') displayName = `PCHP-${device.number}`;
                if (model === 'schp') displayName = `SCHP-${device.number}`;
                if (model === 'cdp') displayName = `CDP-${device.number}`;
                if (model === 'ct') displayName = `CT-${device.number}`;

                return (
                  <TableRow key={device.deviceId} className="bg-[#F9FAFF] border-[#EDEFF9]">
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{displayName}</TableCell>
                    <TableCell className="h-[32px] py-1 px-2 text-left flex justify-start"><StatusIndicator status={status} /></TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{formatValue(power as number)}</TableCell>
                    <TableCell className="h-[32px] text-[#212529] text-[9px] py-1 px-2 text-left">{formatValue(frequency as number)}</TableCell>
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

const PlantEquipmentModal: React.FC<PlantEquipmentModalProps> = ({ isOpen, onClose }) => {
  const { devices, getValue } = useRealtime();
  const [isVisible, setIsVisible] = useState(false);
  const [shouldRender, setShouldRender] = useState(isOpen);

  // Extract equipment from realtime devices
  const equipmentByType = useMemo(() => {
    const types = [
      { model: 'chiller', prefix: 'chiller_' },
      { model: 'pchp', prefix: 'pchp_' },
      { model: 'schp', prefix: 'schp_' },
      { model: 'cdp', prefix: 'cdp_' },
      { model: 'ct', prefix: 'ct_' },
    ];

    const result: Record<string, EquipmentDevice[]> = {};

    types.forEach(type => {
      result[type.model] = Object.keys(devices)
        .filter(deviceId => deviceId.startsWith(type.prefix))
        .map(deviceId => ({
          deviceId,
          number: deviceId.replace(type.prefix, '')
        }))
        .sort((a, b) => {
          const numA = parseInt(a.number) || 0;
          const numB = parseInt(b.number) || 0;
          return numA - numB;
        });
    });

    return result;
  }, [devices]);

  // Get efficiencies from plant-level datapoints
  // Support both efficiency_ch and efficiency_chiller naming
  const chillerEfficiency = (getValue('plant', 'efficiency_ch') ?? getValue('plant', 'efficiency_chiller')) as number || 0;
  const pchpEfficiency = getValue('plant', 'efficiency_pchp') as number || 0;
  const schpEfficiency = getValue('plant', 'efficiency_schp') as number || 0;
  const cdpEfficiency = getValue('plant', 'efficiency_cdp') as number || 0;
  const ctEfficiency = getValue('plant', 'efficiency_ct') as number || 0;

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
              efficiency={chillerEfficiency}
              model="chiller"
              devices={equipmentByType['chiller'] || []}
            />

            <EquipmentSection
              title="PCHP"
              efficiency={pchpEfficiency}
              model="pchp"
              devices={equipmentByType['pchp'] || []}
            />

            <EquipmentSection
              title="SCHP"
              efficiency={schpEfficiency}
              model="schp"
              devices={equipmentByType['schp'] || []}
            />

            <EquipmentSection
              title="CDP"
              efficiency={cdpEfficiency}
              model="cdp"
              devices={equipmentByType['cdp'] || []}
            />

            <EquipmentSection
              title="Cooling Tower"
              efficiency={ctEfficiency}
              model="ct"
              devices={equipmentByType['ct'] || []}
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default PlantEquipmentModal;
