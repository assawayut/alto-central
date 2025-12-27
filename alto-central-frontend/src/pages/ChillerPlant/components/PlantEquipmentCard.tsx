import React, { useState, useMemo } from 'react';
import ChillerImage from "@/assets/chiller_image.png";
import PumpImage from "@/assets/pump_image.png";
import CoolingTowerImage from "@/assets/cooling_tower_image.png";
import PlantEquipmentModal from "./PlantEquipmentModal";
import { RiArrowRightSLine } from "react-icons/ri";
import { useDevice } from '@/contexts/DeviceContext';
import { useRealtime } from '@/features/realtime';
import { OntologyEntity } from '@/features/ontology';
import { useOntologyEntities } from '@/features/ontology';

// Water-side entity interface
interface WaterSideEntity extends OntologyEntity {
  equipmentType: string;
  status: 'normal' | 'off' | 'warning' | 'alarm';
}

interface EquipmentTypeInfo {
  code: string;
  name: string;
  model: string;
  tag: string; // ontology tag to query
}

// Utility functions moved outside component to avoid hoisting issues
const getEquipmentType = (entity: OntologyEntity): string => {
  if (!entity.tags || !entity.tags.model) return 'unknown';
  return String(entity.tags.model);
};

// Extract all numbers after the prefix and join with "-"
const getDeviceNumber = (entityId: string): string => {
  const matches = entityId.match(/\d+/g);
  return matches ? matches.join('-') : entityId;
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

const PlantEquipmentCard: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { isDeviceUnderMaintenance } = useDevice();
  const { getValue } = useRealtime();

  // Fetch water-side equipment using ontology hook
  const { entities: waterEntities, loading: isLoading } = useOntologyEntities({
    tag_filter: 'spaceRef:plant',
    expand: ['tags', 'latest_data']
  });

  const equipmentTypes: EquipmentTypeInfo[] = [
    { code: 'CH', name: 'Chiller', model: 'chiller', tag: 'chiller' },
    { code: 'PCHP', name: 'Primary Chilled Water Pump', model: 'pchp', tag: 'pchp' },
    { code: 'SCHP', name: 'Secondary Chilled Water Pump', model: 'schp', tag: 'schp' },
    { code: 'CDP', name: 'Condenser Water Pump', model: 'cdp', tag: 'cdp' },
    { code: 'CT', name: 'Cooling Tower', model: 'ct', tag: 'ct' },
  ];

  // Convert water entities to WaterSideEntity format
  const waterEquipment = useMemo(() => {
    return waterEntities
      .map((entity): WaterSideEntity => ({
        ...entity,
        equipmentType: getEquipmentType(entity),
        status: getEquipmentStatus(entity)
      }));
  }, [waterEntities]);


  // Function to get status styling
  const getStatusStyling = (entityId: string) => {
    // Check if device is under maintenance
    if (isDeviceUnderMaintenance(entityId)) {
      return {
        bg: 'bg-[#FBDFB2]',
        border: 'border-[#F9C36A]',
        text: 'text-[#FF7A00]',
        hasBorder: true
      };
    }

    // Get status from realtime context
    const statusRead = getValue(entityId, 'status_read');
    const alarm = getValue(entityId, 'alarm');

    if (alarm) {
      return {
        bg: 'bg-[#F7A19B]',
        border: 'border-[#EF4337]',
        text: 'text-[#FFFFFF]',
        hasBorder: true
      };
    }

    switch (statusRead) {
      case 1:
        return {
          bg: 'bg-green/50',
          border: 'border-success',
          text: 'text-success',
          hasBorder: true
        };
      case 0:
        return {
          bg: 'bg-[#EDEFF9]',
          border: '',
          text: 'text-[#B4B4B4]',
          hasBorder: false
        };
      default:
        return {
          bg: 'bg-[#EDEFF9]',
          border: '',
          text: 'text-[#B4B4B4]',
          hasBorder: false
        };
    }
  };

  // Group equipment by type and sort by number
  const groupedEquipment = equipmentTypes.map(type => {
    const items = waterEquipment
      .filter(entity => entity.equipmentType === type.model)
      .sort((a, b) => {
        const numA = getDeviceNumber(a.entity_id);
        const numB = getDeviceNumber(b.entity_id);
        return numA.localeCompare(numB, undefined, { numeric: true });
      });
    
    return {
      ...type,
      items
    };
  });

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
                const styling = getStatusStyling(device.entity_id);
                const deviceNumber = getDeviceNumber(device.entity_id) || '-';
                const isNewRow = index > 0 && index % 8 === 0;
                
                return (
                  <div 
                    key={device.entity_id} 
                    className={`flex justify-center items-center flex-col gap-px pt-0.5 pb-[1px] px-[3px] ${styling.bg} ${styling.hasBorder ? 'border-solid border ' + styling.border : ''} rounded-md w-[33px] ${isNewRow ? 'mt-1' : ''}`}
                  >
                    <img 
                      src={group.model === 'chiller' ? ChillerImage : group.model === 'ct' ? CoolingTowerImage : PumpImage} 
                      className={`w-[28px] h-[21px] object-contain ${styling.text !== 'text-success' && 'grayscale'}`}
                    />
                    <span className={`${styling.text} text-[10px] text-center font-semibold`}>{deviceNumber}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
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
