import React from 'react';
import { useRealtime } from '@/features/realtime';

const WeatherStationCard: React.FC = () => {
  const { getValue, getUnit} = useRealtime();
  
  // Get weather data from the real-time context
  const drybulb = getValue('outdoor_weather_station', 'drybulb_temperature');
  const wetbulb = getValue('outdoor_weather_station', 'wetbulb_temperature');
  const humidity = getValue('outdoor_weather_station', 'humidity');
  
  const drybulbUnit = getUnit('outdoor_weather_station', 'drybulb_temperature');
  const wetbulbUnit = getUnit('outdoor_weather_station', 'wetbulb_temperature');
  
  return (
    <div className="flex flex-col gap-1.5 p-2 alto-card bg-background w-full">
      <div className="flex items-center gap-2">
        <div className="flex flex-col gap-0.5">
          <span className="text-[#065BA9] text-xs font-semibold">Weather Station</span>
        </div>
      </div>
      
      <div className="flex flex-col gap-1">
        {/* Dry Bulb Temperature */}
        <div className="flex justify-between items-center">
          <span className="text-gray-900 text-[10px] leading-[14px] tracking-[-0.05px]">DBT</span>
          <div className="flex items-center px-1.5 bg-gray-50 rounded h-5">
            <span className="text-gray-800 text-[10px]">
              {drybulb === null || drybulb === undefined ? "-" : `${drybulb.toFixed(1)} ${drybulbUnit}`}
            </span>
          </div>
        </div>
        
        {/* Wet Bulb Temperature */}
        <div className="flex justify-between items-center">
          <span className="text-gray-900 text-[10px] leading-[14px] tracking-[-0.05px]">WBT</span>
          <div className="flex items-center px-1.5 bg-gray-50 rounded h-5">
            <span className="text-gray-800 text-[10px]">
              {wetbulb === null || wetbulb === undefined ? "-" : `${wetbulb.toFixed(1)} ${wetbulbUnit}`}
            </span>
          </div>
        </div>
        
        {/* Humidity */}
        <div className="flex justify-between items-center">
          <span className="text-gray-900 text-[10px] leading-[14px] tracking-[-0.05px]">Humidity</span>
          <div className="flex items-center px-1.5 bg-gray-50 rounded h-5">
            <span className="text-gray-800 text-[10px]">
              {humidity === null || humidity === undefined ? "-" : `${humidity.toFixed(1)} %`}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherStationCard;
