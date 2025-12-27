import React from 'react';
import { FiCalendar, FiTool, FiAlertCircle, FiCheckCircle, FiClock } from 'react-icons/fi';

type EventType = 'maintenance' | 'alert' | 'inspection' | 'completed';

interface UpcomingEvent {
  id: string;
  title: string;
  description: string;
  time: string;
  date: string;
  type: EventType;
  equipment?: string;
}

// Mock events data
const mockEvents: UpcomingEvent[] = [
  {
    id: '1',
    title: 'Chiller 2 Maintenance',
    description: 'Scheduled quarterly maintenance',
    time: '09:00',
    date: 'Today',
    type: 'maintenance',
    equipment: 'CH-2',
  },
  {
    id: '2',
    title: 'Filter Replacement',
    description: 'AHU-1 filter replacement due',
    time: '14:00',
    date: 'Today',
    type: 'maintenance',
    equipment: 'AHU-1',
  },
  {
    id: '3',
    title: 'Efficiency Check',
    description: 'Weekly efficiency inspection',
    time: '10:00',
    date: 'Tomorrow',
    type: 'inspection',
  },
  {
    id: '4',
    title: 'CT-3 Inspection',
    description: 'Cooling tower basin cleaning',
    time: '08:00',
    date: 'Dec 29',
    type: 'maintenance',
    equipment: 'CT-3',
  },
  {
    id: '5',
    title: 'Pump Overhaul',
    description: 'PCHP-2 scheduled overhaul',
    time: '07:00',
    date: 'Dec 30',
    type: 'maintenance',
    equipment: 'PCHP-2',
  },
];

const getEventIcon = (type: EventType) => {
  switch (type) {
    case 'maintenance':
      return <FiTool className="w-3.5 h-3.5" />;
    case 'alert':
      return <FiAlertCircle className="w-3.5 h-3.5" />;
    case 'inspection':
      return <FiCalendar className="w-3.5 h-3.5" />;
    case 'completed':
      return <FiCheckCircle className="w-3.5 h-3.5" />;
    default:
      return <FiClock className="w-3.5 h-3.5" />;
  }
};

const getEventColor = (type: EventType) => {
  switch (type) {
    case 'maintenance':
      return 'bg-blue-500';
    case 'alert':
      return 'bg-red-500';
    case 'inspection':
      return 'bg-teal-500';
    case 'completed':
      return 'bg-green-500';
    default:
      return 'bg-gray-500';
  }
};

const getEventBgColor = (type: EventType) => {
  switch (type) {
    case 'maintenance':
      return 'bg-blue-50';
    case 'alert':
      return 'bg-red-50';
    case 'inspection':
      return 'bg-teal-50';
    case 'completed':
      return 'bg-green-50';
    default:
      return 'bg-gray-50';
  }
};

const UpcomingEventsCard: React.FC = () => {
  // Group events by date
  const groupedEvents = mockEvents.reduce((acc, event) => {
    if (!acc[event.date]) {
      acc[event.date] = [];
    }
    acc[event.date].push(event);
    return acc;
  }, {} as Record<string, UpcomingEvent[]>);

  return (
    <div className="alto-card h-full flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <h3 className="text-[#065BA9] text-sm font-semibold">Upcoming Events</h3>
          <span className="text-[10px] text-white bg-[#0E7EE4] px-2 py-0.5 rounded-full">
            {mockEvents.length}
          </span>
        </div>
      </div>

      {/* Horizontal Timeline Header */}
      <div className="px-3 py-2 bg-gray-50 border-b border-gray-100">
        <div className="flex items-center gap-1 overflow-x-auto">
          {Object.keys(groupedEvents).map((date, index) => (
            <React.Fragment key={date}>
              <div className={`flex-shrink-0 px-2 py-1 rounded text-[10px] font-medium ${
                index === 0 ? 'bg-[#0E7EE4] text-white' : 'bg-white text-[#788796] border border-gray-200'
              }`}>
                {date}
              </div>
              {index < Object.keys(groupedEvents).length - 1 && (
                <div className="flex-shrink-0 w-4 h-px bg-gray-300" />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Events List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {Object.entries(groupedEvents).map(([date, events]) => (
          <div key={date}>
            {/* Date Header */}
            <div className="text-[10px] text-[#788796] font-medium mb-2 uppercase tracking-wide">
              {date}
            </div>

            {/* Events for this date */}
            <div className="space-y-2">
              {events.map((event, index) => (
                <div
                  key={event.id}
                  className={`relative pl-4 ${index < events.length - 1 ? 'pb-2' : ''}`}
                >
                  {/* Timeline dot and line */}
                  <div className="absolute left-0 top-0 bottom-0 flex flex-col items-center">
                    <div className={`w-2 h-2 rounded-full ${getEventColor(event.type)} z-10`} />
                    {index < events.length - 1 && (
                      <div className="w-px flex-1 bg-gray-200 mt-1" />
                    )}
                  </div>

                  {/* Event Card */}
                  <div className={`ml-2 p-2 rounded-lg ${getEventBgColor(event.type)} border border-gray-100`}>
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className={`${getEventColor(event.type)} text-white p-1 rounded`}>
                            {getEventIcon(event.type)}
                          </span>
                          <span className="text-[11px] font-semibold text-[#272E3B] truncate">
                            {event.title}
                          </span>
                        </div>
                        <p className="text-[10px] text-[#788796] mt-1 line-clamp-2">
                          {event.description}
                        </p>
                        {event.equipment && (
                          <span className="inline-block mt-1 text-[9px] bg-white px-1.5 py-0.5 rounded border border-gray-200 text-[#0E7EE4] font-medium">
                            {event.equipment}
                          </span>
                        )}
                      </div>
                      <div className="flex-shrink-0 text-right">
                        <span className="text-[10px] text-[#0E7EE4] font-medium">
                          {event.time}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-100">
        <button className="w-full text-center text-[11px] text-[#0E7EE4] font-medium hover:underline">
          View All Events
        </button>
      </div>
    </div>
  );
};

export default UpcomingEventsCard;
