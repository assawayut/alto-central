import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { FiCalendar, FiAlertCircle, FiPlay, FiSquare, FiClock, FiChevronRight, FiZap } from 'react-icons/fi';
import { DateTime } from 'luxon';
import { API_ENDPOINTS } from '../../../config/api';

type EventType = 'schedule' | 'start_chiller_sequence' | 'stop_chiller_sequence' | 'alert' | 'optimization';

interface ActionEvent {
  event_id: string;
  event_type: EventType;
  title: string;
  description: string | null;
  scheduled_time: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  equipment: string[];
  source: string;
  payload: Record<string, unknown>;
}

interface EventsResponse {
  site_id: string;
  events: ActionEvent[];
  total_count: number;
}

const getEventIcon = (type: EventType) => {
  switch (type) {
    case 'start_chiller_sequence': return <FiPlay className="w-3 h-3" />;
    case 'stop_chiller_sequence': return <FiSquare className="w-3 h-3" />;
    case 'schedule': return <FiCalendar className="w-3 h-3" />;
    case 'alert': return <FiAlertCircle className="w-3 h-3" />;
    case 'optimization': return <FiZap className="w-3 h-3" />;
    default: return <FiClock className="w-3 h-3" />;
  }
};

const getEventColor = (type: EventType) => {
  switch (type) {
    case 'start_chiller_sequence': return 'bg-green-500';
    case 'stop_chiller_sequence': return 'bg-orange-500';
    case 'schedule': return 'bg-blue-500';
    case 'alert': return 'bg-red-500';
    case 'optimization': return 'bg-purple-500';
    default: return 'bg-gray-500';
  }
};

const formatEventDate = (isoString: string): string => {
  const dt = DateTime.fromISO(isoString);
  const now = DateTime.now();
  const today = now.startOf('day');
  const tomorrow = today.plus({ days: 1 });
  const eventDay = dt.startOf('day');

  if (eventDay.equals(today)) {
    return 'Today';
  } else if (eventDay.equals(tomorrow)) {
    return 'Tomorrow';
  } else {
    return dt.toFormat('d MMM');
  }
};

const formatEventTime = (isoString: string): string => {
  return DateTime.fromISO(isoString).toFormat('HH:mm');
};

const UpcomingEventsCard: React.FC = () => {
  const { siteId } = useParams<{ siteId: string }>();
  const [events, setEvents] = useState<ActionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!siteId) return;

    const fetchEvents = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.eventsUpcoming(siteId, { limit: 15 }));
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data: EventsResponse = await response.json();
        setEvents(data.events);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch events:', err);
        setError('Failed to load events');
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
    const interval = setInterval(fetchEvents, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [siteId]);

  if (loading) {
    return (
      <div className="alto-card p-3">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[#065BA9] text-sm font-semibold">Upcoming Events</h3>
        </div>
        <div className="flex items-center justify-center py-4 text-sm text-gray-500">
          Loading...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alto-card p-3">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[#065BA9] text-sm font-semibold">Upcoming Events</h3>
        </div>
        <div className="flex items-center justify-center py-4 text-sm text-red-500">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="alto-card p-3">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-[#065BA9] text-sm font-semibold">Upcoming Events</h3>
          <span className="text-[10px] text-white bg-[#0E7EE4] px-1.5 py-0.5 rounded-full">
            {events.length}
          </span>
        </div>
        <button className="text-[10px] text-[#0E7EE4] font-medium hover:underline flex items-center gap-0.5">
          View All <FiChevronRight className="w-3 h-3" />
        </button>
      </div>

      {/* Horizontal Timeline */}
      {events.length === 0 ? (
        <div className="flex items-center justify-center py-4 text-sm text-gray-500">
          No upcoming events
        </div>
      ) : (
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {events.map((event, index) => (
            <React.Fragment key={event.event_id}>
              {/* Event Item */}
              <div className="flex-shrink-0 flex items-center gap-2 px-2 py-1.5 bg-gray-50 rounded-lg border border-gray-100 hover:bg-gray-100 cursor-pointer transition-colors">
                <span className={`${getEventColor(event.event_type)} text-white p-1 rounded`}>
                  {getEventIcon(event.event_type)}
                </span>
                <div className="min-w-0">
                  <div className="text-[10px] text-[#788796]">
                    {formatEventDate(event.scheduled_time)} {formatEventTime(event.scheduled_time)}
                  </div>
                  <div className="text-[11px] font-medium text-[#272E3B] truncate max-w-[100px]">
                    {event.title}
                  </div>
                </div>
              </div>

              {/* Connector line */}
              {index < events.length - 1 && (
                <div className="flex-shrink-0 w-4 h-px bg-gray-300" />
              )}
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
};

export default UpcomingEventsCard;
