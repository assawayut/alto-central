# Upcoming Events API Specification

## Overview

This document specifies the backend API requirements for the Upcoming Events feature in Alto Central. The feature displays scheduled events, equipment sequences, and alerts in a timeline format on the Chiller Plant dashboard.

Reference implementation: `alto-cero-interface/NextEventTimeline.tsx`

## Endpoints

### 1. Get Action Events

Retrieves action events for a site (scheduled, running, and recent completed events).

```
GET /api/v1/sites/{site_id}/action-events/
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | `all` | Filter by status: `all`, `pending`, `running`, `completed`, `failed` |
| `limit` | int | `20` | Maximum number of events to return |
| `hours_ahead` | int | `24` | How far ahead to look for pending events |
| `hours_behind` | int | `2` | How far back to look for completed events |

#### Response

```json
{
  "site_id": "kspo",
  "events": [
    {
      "event_id": "evt_001",
      "event_type": "schedule",
      "title": "Scheduled Maintenance",
      "description": "Monthly chiller inspection",
      "scheduled_time": "2024-01-15T09:00:00+07:00",
      "end_time": "2024-01-15T11:00:00+07:00",
      "status": "pending",
      "equipment": ["chiller_1", "chiller_2"],
      "created_at": "2024-01-10T14:30:00+07:00",
      "updated_at": "2024-01-10T14:30:00+07:00"
    },
    {
      "event_id": "evt_002",
      "event_type": "start_chiller_sequence",
      "title": "Start Chiller Sequence",
      "description": "Ramp up cooling capacity",
      "scheduled_time": "2024-01-15T07:00:00+07:00",
      "status": "completed",
      "equipment": ["chiller_3"],
      "created_at": "2024-01-14T18:00:00+07:00",
      "updated_at": "2024-01-15T07:15:00+07:00",
      "completed_at": "2024-01-15T07:15:00+07:00"
    }
  ],
  "total_count": 2
}
```

### 2. Get Upcoming Schedules (Optional)

Retrieves recurring schedules for a site.

```
GET /api/v1/sites/{site_id}/schedules/upcoming/
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days_ahead` | int | `7` | How many days ahead to look |

#### Response

```json
{
  "site_id": "kspo",
  "schedules": [
    {
      "schedule_id": "sch_001",
      "title": "Weekly Inspection",
      "description": "Check all equipment status",
      "recurrence": "weekly",
      "day_of_week": "monday",
      "time": "09:00",
      "next_occurrence": "2024-01-15T09:00:00+07:00",
      "equipment": []
    }
  ]
}
```

## Data Models

### Event Types

| Type | Description | Color (Frontend) |
|------|-------------|------------------|
| `schedule` | Scheduled maintenance or inspection | Blue |
| `start_chiller_sequence` | Equipment startup sequence | Green |
| `stop_chiller_sequence` | Equipment shutdown sequence | Orange |
| `alert` | AFDD-triggered alert event | Red |
| `optimization` | ML optimization event (future) | Purple |

### Event Status

| Status | Description |
|--------|-------------|
| `pending` | Scheduled but not yet started |
| `running` | Currently in progress |
| `completed` | Successfully finished |
| `failed` | Failed to complete |
| `cancelled` | Manually cancelled |

### Event Object Schema

```typescript
interface ActionEvent {
  event_id: string;
  event_type: 'schedule' | 'start_chiller_sequence' | 'stop_chiller_sequence' | 'alert' | 'optimization';
  title: string;
  description?: string;
  scheduled_time: string;  // ISO 8601 datetime with timezone
  end_time?: string;       // ISO 8601 datetime (for duration-based events)
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  equipment: string[];     // List of device_ids affected
  priority?: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error_message?: string;  // If status is 'failed'
}
```

## Frontend Integration

### Polling Interval

The frontend will poll this endpoint every **10 seconds** (same as realtime data) or can use a longer interval like 30 seconds since events don't change as frequently.

### Display Requirements

1. **Timeline Header**: Horizontal scrollable timeline showing upcoming event times
2. **Event List**: Vertical list grouped by date (Today, Tomorrow, etc.)
3. **Event Cards**: Show title, time, equipment tags, and status indicator
4. **Real-time Updates**: Status changes (pending → running → completed) should reflect on next poll

### Example Frontend Usage

```typescript
// In UpcomingEventsCard.tsx
const fetchEvents = async () => {
  const response = await fetch(
    `${API_BASE_URL}/sites/${siteId}/action-events/?status=all&limit=20`
  );
  const data = await response.json();
  setEvents(data.events);
};

useEffect(() => {
  fetchEvents();
  const interval = setInterval(fetchEvents, 30000); // Poll every 30s
  return () => clearInterval(interval);
}, [siteId]);
```

## Database Considerations

### Suggested Tables

```sql
-- Action Events table
CREATE TABLE action_events (
  event_id UUID PRIMARY KEY,
  site_id VARCHAR(50) NOT NULL,
  event_type VARCHAR(50) NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  scheduled_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  equipment JSONB DEFAULT '[]',
  priority VARCHAR(20) DEFAULT 'medium',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  error_message TEXT,

  INDEX idx_site_status (site_id, status),
  INDEX idx_scheduled_time (scheduled_time)
);

-- Recurring Schedules table (optional)
CREATE TABLE schedules (
  schedule_id UUID PRIMARY KEY,
  site_id VARCHAR(50) NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  recurrence VARCHAR(20) NOT NULL,  -- daily, weekly, monthly
  day_of_week INT,                   -- 0-6 for weekly
  day_of_month INT,                  -- 1-31 for monthly
  time TIME NOT NULL,
  equipment JSONB DEFAULT '[]',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Notes

- All times should be in ISO 8601 format with timezone (site's local timezone preferred)
- Equipment IDs should match device_ids from realtime data (e.g., `chiller_1`, `pchp_2`)
- The `alert` event type can be triggered by AFDD system when faults are detected
- Future: `optimization` events can be created by ML optimization system
