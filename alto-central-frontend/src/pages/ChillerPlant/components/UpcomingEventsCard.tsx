import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { FiCalendar, FiAlertCircle, FiPlay, FiSquare, FiClock, FiChevronRight, FiZap, FiX } from 'react-icons/fi';
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

const getEventIcon = (type: EventType, size: string = 'w-3 h-3') => {
  switch (type) {
    case 'start_chiller_sequence': return <FiPlay className={size} />;
    case 'stop_chiller_sequence': return <FiSquare className={size} />;
    case 'schedule': return <FiCalendar className={size} />;
    case 'alert': return <FiAlertCircle className={size} />;
    case 'optimization': return <FiZap className={size} />;
    default: return <FiClock className={size} />;
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

const getEventTypeLabel = (type: EventType): string => {
  switch (type) {
    case 'start_chiller_sequence': return 'Start Sequence';
    case 'stop_chiller_sequence': return 'Stop Sequence';
    case 'schedule': return 'Schedule';
    case 'alert': return 'Alert';
    case 'optimization': return 'Optimization';
    default: return type;
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

const formatFullDateTime = (isoString: string): string => {
  return DateTime.fromISO(isoString).toFormat('dd/MM/yyyy HH:mm');
};

const formatEquipmentId = (id: string): string => {
  return id.replace(/_/g, '-').toUpperCase();
};

// Event Detail Modal
interface EventDetailModalProps {
  event: ActionEvent;
  onClose: () => void;
}

const EventDetailModal: React.FC<EventDetailModalProps> = ({ event, onClose }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-[400px] max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className={`${getEventColor(event.event_type)} px-4 py-3 flex items-center justify-between`}>
          <div className="flex items-center gap-2 text-white">
            {getEventIcon(event.event_type, 'w-5 h-5')}
            <span className="font-semibold">{getEventTypeLabel(event.event_type)}</span>
          </div>
          <button onClick={onClose} className="text-white/80 hover:text-white">
            <FiX className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4 overflow-y-auto max-h-[60vh]">
          {/* Title */}
          <div>
            <h3 className="text-lg font-semibold text-[#272E3B]">{event.title}</h3>
            {event.description && (
              <p className="text-sm text-[#788796] mt-1">{event.description}</p>
            )}
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-[#788796] text-xs">Scheduled Time</div>
              <div className="font-medium text-[#272E3B]">{formatFullDateTime(event.scheduled_time)}</div>
            </div>
            <div>
              <div className="text-[#788796] text-xs">Status</div>
              <div className="font-medium text-[#272E3B] capitalize">{event.status}</div>
            </div>
            <div>
              <div className="text-[#788796] text-xs">Source</div>
              <div className="font-medium text-[#272E3B]">{event.source}</div>
            </div>
          </div>

          {/* Equipment List */}
          {event.equipment.length > 0 && (
            <div>
              <div className="text-[#788796] text-xs mb-2">Equipment</div>
              <div className="flex flex-wrap gap-1.5">
                {event.equipment.map((eq) => (
                  <span
                    key={eq}
                    className="px-2 py-1 bg-gray-100 rounded text-xs font-medium text-[#272E3B]"
                  >
                    {formatEquipmentId(eq)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Payload Details */}
          {Object.keys(event.payload).length > 0 && (
            <div>
              <div className="text-[#788796] text-xs mb-2">Details</div>
              <div className="bg-gray-50 rounded p-3 space-y-2">
                {Object.entries(event.payload).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-[#788796]">{key.replace(/_/g, ' ')}</span>
                    <span className="font-medium text-[#272E3B]">
                      {Array.isArray(value)
                        ? value.map(v => formatEquipmentId(String(v))).join(', ')
                        : typeof value === 'boolean'
                          ? value ? 'Yes' : 'No'
                          : String(value)
                      }
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const UpcomingEventsCard: React.FC = () => {
  const { siteId } = useParams<{ siteId: string }>();
  const [events, setEvents] = useState<ActionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<ActionEvent | null>(null);

  useEffect(() => {
    if (!siteId) return;

    const fetchEvents = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.eventsUpcoming(siteId, { limit: 15 }));
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data: EventsResponse = await response.json();
        // Filter events: only show events within next 24 hours
        const now = DateTime.now();
        const next24Hours = now.plus({ hours: 24 });
        const futureEvents = data.events.filter(event => {
          const eventTime = DateTime.fromISO(event.scheduled_time);
          return eventTime > now && eventTime <= next24Hours;
        });
        setEvents(futureEvents);
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
    <>
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
                <div
                  className="flex-shrink-0 flex items-center gap-2 px-2 py-1.5 bg-gray-50 rounded-lg border border-gray-100 hover:bg-gray-100 cursor-pointer transition-colors"
                  onClick={() => setSelectedEvent(event)}
                >
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

      {/* Event Detail Modal */}
      {selectedEvent && (
        <EventDetailModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
        />
      )}
    </>
  );
};

export default UpcomingEventsCard;
