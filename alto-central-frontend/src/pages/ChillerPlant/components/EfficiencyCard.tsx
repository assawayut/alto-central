import React from 'react';
import { BarGauge } from "@/components/ui/bar-gauge";
import { useRealtime } from '@/features/realtime';

// Define constants for the gauge
const COLORS = ['#14B8B4', '#FEBE54', '#FF7A00', '#EF4337'];
const LABELS = ['Excellent', 'Good', 'Fair', 'Improve'];

interface EfficiencyCardProps {
  thresholds: number[];
  deviceId: string;
  title: string;
}

const EfficiencyCard: React.FC<EfficiencyCardProps> = ({ 
  thresholds = [0.0, 0.6, 0.7, 0.8, 1.0],
  deviceId = 'plant',
  title = 'Plant Efficiency'
}) => {
  // Use the realtime context to get data
  const { getValue } = useRealtime();
  
  // Calculate efficiency as power / cooling_rate (kW/RT)
  let efficiencyValue: number | undefined = undefined;
  
  if (deviceId === 'plant') {
    // Plant efficiency: plant_power / plant_cooling_rate
    const coolingRate = getValue(deviceId, 'cooling_rate');
    const power = getValue(deviceId, 'power');
    
    if (coolingRate !== undefined && power !== undefined && coolingRate > 30) {
      efficiencyValue = power / coolingRate;
    }
  } else if (deviceId === 'air_distribution_system') {
    // Air-side efficiency: air_power / plant_cooling_rate
    const airPower = getValue(deviceId, 'power');
    const plantCoolingRate = getValue('plant', 'cooling_rate');
    
    if (airPower !== undefined && plantCoolingRate !== undefined && plantCoolingRate > 30) {
      efficiencyValue = airPower / plantCoolingRate;
    }
  }
  
  return (
    <div className="w-full h-full p-[10px] alto-card bg-background">
      <div className="flex flex-col">
        {/* Title Row */}
        <div className="w-full flex justify-between items-center">
          <h2 className="text-card-foreground text-lg font-semibold tracking-[0.01em]">
            {title}
          </h2>
        </div>
        
        {/* BarGauge Container */}
        <div className="w-full flex flex-col justify-end items-center gap-0.5 min-h-[50px]">
          <div className="w-full max-w-full">
            <BarGauge
              labels={LABELS}
              colors={COLORS}
              value={efficiencyValue}
              threshold={thresholds}
              showValue={true}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EfficiencyCard;
