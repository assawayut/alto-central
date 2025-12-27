import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useRealtime } from '@/features/realtime';
import { API_ENDPOINTS } from '@/config/api';
import { getSiteById } from '@/config/sites';

interface EnergyDailyResponse {
  site_id: string;
  yesterday: {
    total: number | null;
    plant: number | null;
    air_side: number | null;
  };
  today: {
    total: number | null;
    plant: number | null;
    air_side: number | null;
  };
  unit: string;
}

interface DayColumnProps {
  title: string;
  total: number | null;
  plant: number | null;
  airSide: number | null;
  dbt: number | null;
  rh: number | null;
  showAirSide: boolean;
}

const DayColumn: React.FC<DayColumnProps> = ({ title, total, plant, airSide, dbt, rh, showAirSide }) => {
  const formatValue = (value: number | null) => {
    if (value === null || value === undefined || isNaN(value)) return '-';
    return value.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
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

        {showAirSide && (
          <div className="flex justify-between items-center">
            <span className="text-[#0E7EE4] text-xs">Air-Side</span>
            <div className="flex items-baseline gap-1">
              <span className="text-[#272E3B] text-sm font-semibold">{formatValue(airSide)}</span>
              <span className="text-[#788796] text-[10px]">kWh</span>
            </div>
          </div>
        )}
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
  const { siteId } = useParams<{ siteId: string }>();
  const { getValue } = useRealtime();
  const [energyData, setEnergyData] = useState<EnergyDailyResponse | null>(null);

  // Get site config to check hvac_type
  const site = getSiteById(siteId || '');
  const showAirSide = site?.hvac_type !== 'water';

  useEffect(() => {
    if (!siteId) return;

    const fetchEnergy = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.energyDaily(siteId));
        if (response.ok) {
          const data = await response.json();
          setEnergyData(data);
        }
      } catch (err) {
        console.error('Failed to fetch energy data:', err);
      }
    };

    fetchEnergy();
  }, [siteId]);

  // Yesterday values from API
  const yesterdayTotal = energyData?.yesterday?.total ?? null;
  const yesterdayPlant = energyData?.yesterday?.plant ?? null;
  const yesterdayAirSide = energyData?.yesterday?.air_side ?? null;

  // Today values from API
  const todayTotal = energyData?.today?.total ?? null;
  const todayPlant = energyData?.today?.plant ?? null;
  const todayAirSide = energyData?.today?.air_side ?? null;

  // Weather from real-time data
  const todayDBT = getValue('outdoor_weather_station', 'drybulb_temperature') as number ?? null;
  const todayRH = getValue('outdoor_weather_station', 'humidity') as number ?? null;

  return (
    <div className="p-3 alto-card">
      <div className="text-[#065BA9] text-sm font-semibold mb-3">Energy Usage</div>

      <div className="flex gap-4">
        <DayColumn
          title="Yesterday"
          total={yesterdayTotal}
          plant={yesterdayPlant}
          airSide={yesterdayAirSide}
          dbt={null}
          rh={null}
          showAirSide={showAirSide}
        />

        <div className="w-px bg-gray-200" />

        <DayColumn
          title="Today"
          total={todayTotal}
          plant={todayPlant}
          airSide={todayAirSide}
          dbt={todayDBT}
          rh={todayRH}
          showAirSide={showAirSide}
        />
      </div>
    </div>
  );
};

export default EnergyUsageCard;
