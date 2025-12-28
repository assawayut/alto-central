import { FiZap, FiCpu, FiTrendingDown, FiSettings } from 'react-icons/fi';

const OptimizationCard: React.FC = () => {
  return (
    <div className="alto-card p-3">
      <div className="flex items-center justify-between mb-3">
        <div className="text-[#065BA9] text-sm font-semibold">Optimization</div>
        <FiZap className="w-4 h-4 text-[#788796]" />
      </div>

      {/* Placeholder features */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg opacity-50">
          <FiCpu className="w-4 h-4 text-[#0E7EE4]" />
          <div>
            <div className="text-[11px] font-medium text-[#272E3B]">AI Sequencing</div>
            <div className="text-[9px] text-[#788796]">Optimal chiller staging</div>
          </div>
        </div>

        <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg opacity-50">
          <FiTrendingDown className="w-4 h-4 text-[#22c55e]" />
          <div>
            <div className="text-[11px] font-medium text-[#272E3B]">Energy Savings</div>
            <div className="text-[9px] text-[#788796]">Setpoint optimization</div>
          </div>
        </div>

        <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg opacity-50">
          <FiSettings className="w-4 h-4 text-[#f59e0b]" />
          <div>
            <div className="text-[11px] font-medium text-[#272E3B]">Auto-Tuning</div>
            <div className="text-[9px] text-[#788796]">PID loop optimization</div>
          </div>
        </div>
      </div>

      <div className="text-[10px] text-[#788796] mt-3 text-center border-t pt-2">
        Coming Soon
      </div>
    </div>
  );
};

export default OptimizationCard;
