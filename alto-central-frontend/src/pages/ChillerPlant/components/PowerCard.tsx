import { useRealtime } from '@/features/realtime';

interface PowerCardProps {
  deviceId: string;
  title: string;
}

export function PowerCard({ deviceId = 'plant', title = 'Plant Power' }: PowerCardProps) {
  // Mock data waiting for real-time API
  const { getValue } = useRealtime();
  const power = getValue(deviceId, 'power');
  const unit = 'kW';

  return (
    <div className="w-full h-full p-2 alto-card flex flex-col justify-between items-start overflow-hidden bg-background">
      <div className="w-full flex justify-start items-center overflow-x-auto">
        <div className="flex-shrink-0">
          <div className="text-[#065BA9] text-sm font-semibold whitespace-nowrap">
            {title}
          </div>
        </div>
      </div>
      
      <div className="w-full flex flex-col justify-start items-start overflow-x-auto">
        <div className="text-[#0E7EE4] text-[28px] sm:text-[32px] font-semibold whitespace-nowrap">
          {power == null ? '-' : power.toFixed(0).toLocaleString()}
        </div>
        <div className="text-[#788796] text-[13px] font-normal whitespace-nowrap">
          {unit}
        </div>
      </div>
    </div>
  );
} 

export default PowerCard;