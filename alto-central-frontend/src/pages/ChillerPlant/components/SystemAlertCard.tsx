import { FC, useEffect } from "react";
import { FiAlertTriangle } from "react-icons/fi";
import { FaCheck } from "react-icons/fa";
import { RiArrowRightSLine } from "react-icons/ri";
import { useNavigate } from "react-router-dom";
import { useAFDDAlertSummary, type CategoryAlertSummary } from "@/features/afdd/hooks";

interface AlertBoxProps {
  level: string;
  count: number;
  borderColor: string;
  bgColor: string;
  textColor: string;
  badgeColor: string;
}

interface AlertSectionProps {
  title: string;
  alerts: AlertBoxProps[];
}

const AlertBox: FC<AlertBoxProps> = ({
  level,
  count,
  borderColor,
  bgColor,
  textColor,
  badgeColor,
}) => (
  <div
    className={`py-[2px] pl-[5px] pr-[8px] rounded-md border ${borderColor} ${bgColor} flex items-center gap-[6px] w-full`}
  >
    <div
      className={`border rounded-full w-[14px] h-[14px] flex items-center justify-center ${badgeColor}`}
    >
      <FiAlertTriangle size={7} color="white" />
    </div>
    <p className="text-[11px]">{level}</p>
    <p className={`text-[12px] font-semibold ${textColor}`}>{count}</p>
  </div>
);

const AlertSection: FC<AlertSectionProps> = ({ title, alerts }) => {
  // Check if any alert count is undefined
  const hasUndefinedCount = alerts.some(alert => alert.count === undefined);
  
  if (hasUndefinedCount) {
    return (
      <div className="mt-[10px]">
        <p className="text-[10px] text-[#788796] font-semibold">{title}</p>
        <div className="flex items-center gap-[8px] mt-[6px]">
          <div className="py-[3px] px-[7px] rounded-[400px] border border-[#DDDDDD] bg-[#DDDDDD4D] flex items-center gap-[2px] w-full justify-center">
            <p className="text-[10px] text-[#788796] font-[400]">-</p>
          </div>
        </div>
      </div>
    );
  }

  const hasActiveAlerts = alerts.some(alert => alert.count > 0);
  const activeAlertsCount = alerts.filter(alert => alert.count > 0).length;

  return (
    <div className="mt-[10px]">
      <p className="text-[10px] text-[#788796] font-semibold">{title}</p>
      <div className="flex items-center gap-[8px] mt-[6px]">
        {hasActiveAlerts ? (
          <div className={`flex items-center gap-[8px] ${activeAlertsCount === 3 ? 'w-full' : ''}`}>
            {alerts.map((alert, index) => 
              alert.count > 0 && (
                <AlertBox
                  key={index}
                  level={alert.level}
                  count={alert.count}
                  borderColor={alert.borderColor}
                  bgColor={alert.bgColor}
                  textColor={alert.textColor}
                  badgeColor={alert.badgeColor}
                />
              )
            )}
          </div>
        ) : (
          <div className="py-[3px] px-[7px] rounded-[400px] border border-[#59D1CE] bg-[#CBF0EF] flex items-center gap-[2px] w-full justify-center">
            <div className="border rounded-full w-[14px] h-[14px] flex items-center justify-center bg-[#14B8B4]">
              <FaCheck size={7} color="white" />
            </div>
            <p className="text-[10px] text-[#14B0BC] font-[400]">System Running Normally</p>
          </div>
        )}
      </div>
    </div>
  );
};

const SystemAlertCard: FC = () => {
  const navigate = useNavigate();
  const { categories, isLoading, error, refetch } = useAFDDAlertSummary();

  // Auto-refresh every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      refetch();
    }, 10000); // 10 seconds

    return () => clearInterval(interval);
  }, [refetch]);

  const getCategoryAlerts = (category: CategoryAlertSummary) => {
    return [
      {
        level: "Critical",
        count: category.critical,
        borderColor: "border-[#FF5A5A]",
        bgColor: "bg-[#FFE5E5]",
        textColor: "text-[#FF5A5A]",
        badgeColor: "bg-[#FF5A5A]",
      },
      {
        level: "Warning",
        count: category.warning,
        borderColor: "border-[#FF9F1C]",
        bgColor: "bg-[#FFF5E5]",
        textColor: "text-[#FF9F1C]",
        badgeColor: "bg-[#FF9F1C]",
      },
      {
        level: "Info",
        count: category.info,
        borderColor: "border-[#0E7EE4]",
        bgColor: "bg-[#E5F2FF]",
        textColor: "text-[#0E7EE4]",
        badgeColor: "bg-[#0E7EE4]",
      },
    ];
  };

  // Transform AFDD categories into alert data structure
  const alertData = categories
    .filter(category => category.total > 0 || !isLoading) // Show all categories, or only active ones when loaded
    .map(category => ({
      title: `${category.category.replace('-', ' ')} Systems`,
      alerts: getCategoryAlerts(category),
    }));

  // Show loading or error state if needed
  if (isLoading) {
    return (
      <div className="p-[10px] alto-card">
        <div className="flex justify-between items-center">
          <p className="text-[#065BA9] font-semibold">System & Machine Alerts</p>
          <button
            className="h-[36px] w-[36px] bg-white4 rounded-[6px] flex justify-center items-center hover:bg-card"
            onClick={() => navigate('/app/afdd')}
          >
            <RiArrowRightSLine
              className="h-[24px] w-[24px]"
              color="#065BA9"
            />
          </button>
        </div>
        <div className="mt-[10px] flex items-center justify-center py-4">
          <p className="text-[10px] text-[#788796]">Loading alerts...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-[10px] alto-card">
        <div className="flex justify-between items-center">
          <p className="text-[#065BA9] font-semibold">System & Machine Alerts</p>
          <button
            className="h-[36px] w-[36px] bg-white4 rounded-[6px] flex justify-center items-center hover:bg-card"
            onClick={() => navigate('/app/afdd')}
          >
            <RiArrowRightSLine
              className="h-[24px] w-[24px]"
              color="#065BA9"
            />
          </button>
        </div>
        <div className="mt-[10px] flex items-center justify-center py-4">
          <p className="text-[10px] text-red-600">Failed to load alerts</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-[10px] alto-card">
      <div className="flex justify-between items-center">
        <p className="text-[#065BA9] font-semibold">System & Machine Alerts</p>
        <button
          className="h-[36px] w-[36px] bg-white4 rounded-[6px] flex justify-center items-center hover:bg-card"
          onClick={() => navigate('/app/afdd')}
        >
          <RiArrowRightSLine
            className="h-[24px] w-[24px]"
            color="#065BA9"
          />
        </button>
      </div>
      {alertData.map((section, index) => (
        <AlertSection key={index} title={section.title} alerts={section.alerts} />
      ))}
    </div>
  );
};

export default SystemAlertCard;
