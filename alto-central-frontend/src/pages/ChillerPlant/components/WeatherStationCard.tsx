import React from 'react';
import { useRealtime } from '@/features/realtime';

const WeatherStationCard: React.FC = () => {
  const { getValue } = useRealtime();

  // Get weather data from the real-time context
  const drybulb = getValue('outdoor_weather_station', 'drybulb_temperature') as number;
  const wetbulb = getValue('outdoor_weather_station', 'wetbulb_temperature') as number;
  const humidity = getValue('outdoor_weather_station', 'humidity') as number;

  return (
    <div className="flex flex-col gap-2 p-3 alto-card bg-background w-full h-full">
      <div className="text-[#065BA9] text-sm font-semibold">Weather Station</div>

      {/* Current Conditions - Inline style */}
      <div className="space-y-1.5">
        <div className="flex items-center gap-2">
          <span className="text-[#272E3B] text-xs min-w-[60px]">DBT</span>
          <span className="text-[#0E7EE4] text-sm font-semibold">
            {drybulb === null || drybulb === undefined ? '-' : `${drybulb.toFixed(1)} °F`}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[#272E3B] text-xs min-w-[60px]">WBT</span>
          <span className="text-[#0E7EE4] text-sm font-semibold">
            {wetbulb === null || wetbulb === undefined ? '-' : `${wetbulb.toFixed(1)} °F`}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[#272E3B] text-xs min-w-[60px]">Humidity</span>
          <span className="text-[#0E7EE4] text-sm font-semibold">
            {humidity === null || humidity === undefined ? '-' : `${humidity.toFixed(1)} %`}
          </span>
        </div>
      </div>
    </div>
  );
};

export default WeatherStationCard;
