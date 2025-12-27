import React from 'react';
import { useRealtime } from '@/features/realtime';

interface DayColumnProps {
  title: string;
  total: number | null;
  plant: number | null;
  airSide: number | null;
  dbt: number | null;
  rh: number | null;
}

const DayColumn: React.FC<DayColumnProps> = ({ title, total, plant, airSide, dbt, rh }) => {
  const formatValue = (value: number | null) => {
    if (value === null || value === undefined || isNaN(value)) return 'NaN';
    return value.toLocaleString();
  };

  return (
    <div className="flex-1">
      <div className="text-[#788796] text-xs mb-2">{title}</div>

      <div className="space-y-1">
        <div className="flex justify-between items-center">
          <span className="text-[#272E3B] text-xs">Total</span>
          <div className="flex items-baseline gap-1">
            <span className="text-[#0E7EE4] text-sm font-semibold">{formatValue(total)}</span>
            <span className="text-[#788796] text-[10px]">kWh</span>
          </div>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-[#0E7EE4] text-xs">Plant</span>
          <div className="flex items-baseline gap-1">
            <span className="text-[#0E7EE4] text-sm font-semibold">{formatValue(plant)}</span>
            <span className="text-[#788796] text-[10px]">kWh</span>
          </div>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-[#0E7EE4] text-xs">Air-Side</span>
          <div className="flex items-baseline gap-1">
            <span className="text-[#272E3B] text-sm font-semibold">{formatValue(airSide)}</span>
            <span className="text-[#788796] text-[10px]">kWh</span>
          </div>
        </div>
      </div>

      {/* DBT and RH */}
      <div className="flex gap-2 mt-2 pt-2 border-t border-gray-100">
        <div className="flex items-center gap-1">
          <span className="text-[#788796] text-[10px]">DBT</span>
          <span className="text-[#0E7EE4] text-[10px] font-medium">
            {dbt !== null ? `${dbt.toFixed(1)} °F` : '-'}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[#788796] text-[10px]">RH</span>
          <span className="text-[#0E7EE4] text-[10px] font-medium">
            {rh !== null ? `${rh.toFixed(1)} %` : '-'}
          </span>
        </div>
      </div>
    </div>
  );
};

const EnergyUsageCard: React.FC = () => {
  const { getValue } = useRealtime();

  // Mock data for energy usage - in real implementation, this would come from timeseries API
  // Yesterday values (mock)
  const yesterdayTotal = 2930;
  const yesterdayPlant = 2930;
  const yesterdayAirSide = 0;
  const yesterdayDBT = 85.3;
  const yesterdayRH = 55.4;

  // Today values - use real-time data where available
  const todayPlant = 844;
  const todayAirSide = getValue('air_distribution_system', 'power') as number || null;
  const todayTotal = todayPlant + (todayAirSide || 0);
  const todayDBT = getValue('outdoor_weather_station', 'drybulb_temperature') as number;
  const todayRH = getValue('outdoor_weather_station', 'humidity') as number;

  return (
    <div className="p-3 alto-card">
      <div className="text-[#065BA9] text-sm font-semibold mb-3">Energy Usage</div>

      <div className="flex gap-4">
        <DayColumn
          title="Yesterday"
          total={yesterdayTotal}
          plant={yesterdayPlant}
          airSide={yesterdayAirSide}
          dbt={yesterdayDBT}
          rh={yesterdayRH}
        />

        <div className="w-px bg-gray-200" />

        <DayColumn
          title="Today"
          total={todayTotal}
          plant={todayPlant}
          airSide={todayAirSide}
          dbt={todayDBT}
          rh={todayRH}
        />
      </div>
    </div>
  );
};

export default EnergyUsageCard;
