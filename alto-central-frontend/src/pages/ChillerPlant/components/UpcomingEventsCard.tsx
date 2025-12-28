import React from 'react';
import { FiCalendar, FiTool, FiAlertCircle, FiCheckCircle, FiClock, FiChevronRight } from 'react-icons/fi';

type EventType = 'maintenance' | 'alert' | 'inspection' | 'completed';

interface UpcomingEvent {
  id: string;
  title: string;
  time: string;
  date: string;
  type: EventType;
  equipment?: string;
}

// Mock events data
const mockEvents: UpcomingEvent[] = [
  { id: '1', title: 'CH-2 Maintenance', time: '09:00', date: 'Today', type: 'maintenance', equipment: 'CH-2' },
  { id: '2', title: 'Filter Replace', time: '14:00', date: 'Today', type: 'maintenance', equipment: 'AHU-1' },
  { id: '3', title: 'Efficiency Check', time: '10:00', date: 'Tomorrow', type: 'inspection' },
  { id: '4', title: 'CT-3 Cleaning', time: '08:00', date: 'Dec 29', type: 'maintenance', equipment: 'CT-3' },
  { id: '5', title: 'Pump Overhaul', time: '07:00', date: 'Dec 30', type: 'maintenance', equipment: 'PCHP-2' },
];

const getEventIcon = (type: EventType) => {
  switch (type) {
    case 'maintenance': return <FiTool className="w-3 h-3" />;
    case 'alert': return <FiAlertCircle className="w-3 h-3" />;
    case 'inspection': return <FiCalendar className="w-3 h-3" />;
    case 'completed': return <FiCheckCircle className="w-3 h-3" />;
    default: return <FiClock className="w-3 h-3" />;
  }
};

const getEventColor = (type: EventType) => {
  switch (type) {
    case 'maintenance': return 'bg-blue-500';
    case 'alert': return 'bg-red-500';
    case 'inspection': return 'bg-teal-500';
    case 'completed': return 'bg-green-500';
    default: return 'bg-gray-500';
  }
};

const UpcomingEventsCard: React.FC = () => {
  return (
    <div className="alto-card p-3">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-[#065BA9] text-sm font-semibold">Upcoming Events</h3>
          <span className="text-[10px] text-white bg-[#0E7EE4] px-1.5 py-0.5 rounded-full">
            {mockEvents.length}
          </span>
        </div>
        <button className="text-[10px] text-[#0E7EE4] font-medium hover:underline flex items-center gap-0.5">
          View All <FiChevronRight className="w-3 h-3" />
        </button>
      </div>

      {/* Horizontal Timeline */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {mockEvents.map((event, index) => (
          <React.Fragment key={event.id}>
            {/* Event Item */}
            <div className="flex-shrink-0 flex items-center gap-2 px-2 py-1.5 bg-gray-50 rounded-lg border border-gray-100 hover:bg-gray-100 cursor-pointer transition-colors">
              <span className={`${getEventColor(event.type)} text-white p-1 rounded`}>
                {getEventIcon(event.type)}
              </span>
              <div className="min-w-0">
                <div className="text-[10px] text-[#788796]">{event.date} {event.time}</div>
                <div className="text-[11px] font-medium text-[#272E3B] truncate max-w-[100px]">
                  {event.title}
                </div>
              </div>
            </div>

            {/* Connector line */}
            {index < mockEvents.length - 1 && (
              <div className="flex-shrink-0 w-4 h-px bg-gray-300" />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default UpcomingEventsCard;
