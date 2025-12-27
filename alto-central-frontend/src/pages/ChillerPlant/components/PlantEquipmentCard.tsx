import React, { useState, useMemo } from 'react';
import ChillerImage from "@/assets/chiller_image.png";
import PumpImage from "@/assets/pump_image.png";
import CoolingTowerImage from "@/assets/cooling_tower_image.png";
import PlantEquipmentModal from "./PlantEquipmentModal";
import { RiArrowRightSLine } from "react-icons/ri";
import { useDevice } from '@/contexts/DeviceContext';
import { useRealtime } from '@/features/realtime';

interface EquipmentTypeInfo {
  code: string;
  name: string;
  prefix: string;  // Device ID prefix to match (e.g., 'chiller_', 'pchp_')
  image: string;
}

interface EquipmentDevice {
  deviceId: string;
  number: string;
  status: 'running' | 'standby' | 'alarm';
}

const PlantEquipmentCard: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { isDeviceUnderMaintenance } = useDevice();
  const { devices, getValue, isLoading } = useRealtime();

  const equipmentTypes: EquipmentTypeInfo[] = [
    { code: 'CH', name: 'Chiller', prefix: 'chiller_', image: ChillerImage },
    { code: 'PCHP', name: 'Primary Chilled Water Pump', prefix: 'pchp_', image: PumpImage },
    { code: 'SCHP', name: 'Secondary Chilled Water Pump', prefix: 'schp_', image: PumpImage },
    { code: 'CDP', name: 'Condenser Water Pump', prefix: 'cdp_', image: PumpImage },
    { code: 'CT', name: 'Cooling Tower', prefix: 'ct_', image: CoolingTowerImage },
  ];

  // Extract equipment from realtime devices
  const groupedEquipment = useMemo(() => {
    return equipmentTypes.map(type => {
      // Find all devices matching this prefix
      const items: EquipmentDevice[] = Object.keys(devices)
        .filter(deviceId => deviceId.startsWith(type.prefix))
        .map(deviceId => {
          // Extract number from device ID (e.g., 'chiller_1' -> '1')
          const number = deviceId.replace(type.prefix, '');

          // Get status
          const statusRead = getValue(deviceId, 'status_read');
          const alarm = getValue(deviceId, 'alarm');

          let status: 'running' | 'standby' | 'alarm' = 'standby';
          if (alarm === 1) {
            status = 'alarm';
          } else if (statusRead === 1) {
            status = 'running';
          }

          return { deviceId, number, status };
        })
        .sort((a, b) => {
          // Sort by number
          const numA = parseInt(a.number) || 0;
          const numB = parseInt(b.number) || 0;
          return numA - numB;
        });

      return { ...type, items };
    }).filter(group => group.items.length > 0); // Only show groups with equipment
  }, [devices, getValue]);

  // Function to get status styling
  const getStatusStyling = (deviceId: string, status: 'running' | 'standby' | 'alarm') => {
    // Check if device is under maintenance
    if (isDeviceUnderMaintenance(deviceId)) {
      return {
        bg: 'bg-[#FBDFB2]',
        border: 'border-[#F9C36A]',
        text: 'text-[#FF7A00]',
        hasBorder: true,
        grayscale: true
      };
    }

    switch (status) {
      case 'alarm':
        return {
          bg: 'bg-[#F7A19B]',
          border: 'border-[#EF4337]',
          text: 'text-[#FFFFFF]',
          hasBorder: true,
          grayscale: true
        };
      case 'running':
        return {
          bg: 'bg-green/50',
          border: 'border-success',
          text: 'text-success',
          hasBorder: true,
          grayscale: false
        };
      default: // standby
        return {
          bg: 'bg-[#EDEFF9]',
          border: '',
          text: 'text-[#B4B4B4]',
          hasBorder: false,
          grayscale: true
        };
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col alto-card p-[10px] h-full bg-background overflow-hidden">
        <div className="flex items-center pb-[8px] gap-1">
          <span className="text-[#065BA9] text-xs font-semibold">System Status</span>
        </div>
        <div className="flex justify-center items-center h-full">
          <span className="text-muted text-sm">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col alto-card p-[10px] h-full bg-background overflow-hidden">
      <div className="flex items-center pb-[8px] gap-1">
        <span className="text-[#065BA9] text-xs font-semibold">System Status</span>
        <button
          className="h-[24px] w-[24px] bg-white4 rounded-[6px] flex justify-center items-center hover:bg-card"
          onClick={() => setIsModalOpen(true)}
        >
          <RiArrowRightSLine
            className="h-[12px] w-[12px]"
            color="#065BA9"
          />
        </button>
      </div>

      <div className="flex justify-center items-start flex-col gap-1.5 flex-grow">
        {groupedEquipment.map((group) => (
          <div key={group.code} className="flex justify-center items-start flex-col gap-0.5">
            <div className="flex self-stretch justify-start items-center flex-row gap-2">
              <span className="text-[#5E5E5E] text-xs font-semibold">{group.code}</span>
              <span className="text-[#788796] text-[10px]">{group.name}</span>
            </div>
            <div className="flex self-stretch justify-start items-center flex-wrap gap-1">
              {group.items.map((device, index) => {
                const styling = getStatusStyling(device.deviceId, device.status);
                const isNewRow = index > 0 && index % 8 === 0;

                return (
                  <div
                    key={device.deviceId}
                    className={`flex justify-center items-center flex-col gap-px pt-0.5 pb-[1px] px-[3px] ${styling.bg} ${styling.hasBorder ? 'border-solid border ' + styling.border : ''} rounded-md w-[33px] ${isNewRow ? 'mt-1' : ''}`}
                  >
                    <img
                      src={group.image}
                      className={`w-[28px] h-[21px] object-contain ${styling.grayscale ? 'grayscale' : ''}`}
                    />
                    <span className={`${styling.text} text-[10px] text-center font-semibold`}>{device.number}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}

        {groupedEquipment.length === 0 && (
          <div className="flex justify-center items-center w-full h-full">
            <span className="text-muted text-sm">No equipment data</span>
          </div>
        )}
      </div>

      <div className="flex justify-start items-center flex-row gap-2 mt-[10px]">
        <div className="flex justify-center items-center flex-row gap-1">
          <div className="bg-muted rounded-[100px] w-[6px] h-[6px]" style={{ width: '6px' }}></div>
          <span className="text-muted text-[8px]">Standby</span>
        </div>
        <div className="flex justify-center items-center flex-row gap-1">
          <div className="bg-green rounded-[100px] w-[6px] h-[6px]" style={{ width: '6px' }}></div>
          <span className="text-muted text-[8px]">Running</span>
        </div>
        <div className="flex justify-center items-center flex-row gap-1">
          <div className="bg-warning rounded-[100px] w-[6px] h-[6px]" style={{ width: '6px' }}></div>
          <span className="text-muted text-[8px]">Maintenance</span>
        </div>
        <div className="flex justify-center items-center flex-row gap-1">
          <div className="bg-danger rounded-[100px] w-[6px] h-[6px]" style={{ width: '6px' }}></div>
          <span className="text-muted text-[8px]">Alarm</span>
        </div>
      </div>

      {/* Plant Equipment Modal */}
      <PlantEquipmentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
};

export default PlantEquipmentCard;
