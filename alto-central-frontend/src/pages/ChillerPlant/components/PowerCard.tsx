import { useRealtime } from '@/features/realtime';
import { FiInfo } from 'react-icons/fi';

interface PowerCardProps {
  deviceId?: string;
  title?: string;
}

export function PowerCard({ deviceId = 'plant' }: PowerCardProps) {
  const { getValue } = useRealtime();

  const power = getValue(deviceId, 'power') as number;
  const coolingLoad = getValue(deviceId, 'cooling_rate') as number;
  // Part-load comes from API as percentage
  const partLoad = getValue(deviceId, 'running_capacity') as number ?? 0;

  return (
    <div className="w-full h-full alto-card flex items-stretch overflow-hidden bg-background">
      {/* Plant Power */}
      <div className="flex-1 p-3 flex flex-col justify-between">
        <div className="text-[#065BA9] text-sm font-semibold">Plant Power</div>
        <div>
          <div className="text-[#0E7EE4] text-[32px] font-semibold leading-tight">
            {power == null ? '-' : power.toFixed(0)}
          </div>
          <div className="text-[#788796] text-xs">kW</div>
        </div>
      </div>

      {/* Divider */}
      <div className="w-px bg-gray-200 my-2" />

      {/* Cooling Load */}
      <div className="flex-1 p-3 flex flex-col justify-between">
        <div className="text-[#065BA9] text-sm font-semibold">Cooling Load</div>
        <div>
          <div className="text-[#0E7EE4] text-[32px] font-semibold leading-tight">
            {coolingLoad == null ? '-' : coolingLoad.toFixed(0)}
          </div>
          <div className="text-[#788796] text-xs">RT</div>
        </div>
      </div>

      {/* Divider */}
      <div className="w-px bg-gray-200 my-2" />

      {/* Part-Load */}
      <div className="flex-1 p-3 flex flex-col justify-between">
        <div className="flex items-center gap-1">
          <span className="text-[#788796] text-sm font-medium">Part-Load</span>
          <FiInfo className="w-3.5 h-3.5 text-[#0E7EE4]" />
        </div>
        <div>
          <div className="flex items-baseline gap-1">
            <span className="text-[#0E7EE4] text-[28px] font-semibold leading-tight">
              {partLoad.toFixed(1)}
            </span>
            <span className="text-[#788796] text-sm">%</span>
          </div>
          {/* Progress bar */}
          <div className="mt-2 w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-[#0E7EE4] rounded-full transition-all duration-300"
              style={{ width: `${Math.min(partLoad, 100)}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default PowerCard;
