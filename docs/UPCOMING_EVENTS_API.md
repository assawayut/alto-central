# Upcoming Events API Specification

## Overview

This document specifies the backend API for the Upcoming Events feature in Alto Central. The feature displays scheduled events, equipment sequences, and alerts in a timeline format on the Chiller Plant dashboard.

**Status: IMPLEMENTED** - Backend reads from MongoDB `control.action_event` collection.

Reference implementation: `alto-cero-interface/NextEventTimeline.tsx`

---

## Endpoints

### 1. Get Action Events

Retrieves action events for a site (scheduled, running, and completed events).

```
GET /api/v1/sites/{site_id}/events/
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | `all` | Filter by status: `all`, `pending`, `in-progress`, `completed`, `failed` |
| `limit` | int | `20` | Maximum number of events to return (max: 100) |

#### Response

```json
{
  "site_id": "kspo",
  "events": [
    {
      "event_id": "AUTO-SCHEDULE-2025Dec28-1700-Priority3-stop_chiller_sequence",
      "event_type": "stop_chiller_sequence",
      "title": "Stop CHILLER-4",
      "description": null,
      "scheduled_time": "2025-12-28T17:00:00+07:00",
      "status": "pending",
      "equipment": ["chiller_4", "cdp_4", "pchp_4"],
      "source": "chillerplantschedule",
      "payload": {
        "chiller_id": "chiller_4",
        "group_equipment": ["pchp_4", "cdp_4"],
        "priority_index": 2,
        "post_circulation": true,
        "post_circulation_delay": 1800
      }
    },
    {
      "event_id": "AUTO-SCHEDULE-2025Dec29-0500-Priority1-start_chiller_sequence",
      "event_type": "start_chiller_sequence",
      "title": "Start CHILLER-1",
      "description": null,
      "scheduled_time": "2025-12-29T05:00:00+07:00",
      "status": "pending",
      "equipment": ["chiller_1", "pchp_1", "cdp_1"],
      "source": "chillerplantschedule",
      "payload": {
        "chiller_id": "chiller_1",
        "group_equipment": ["pchp_1", "cdp_1"],
        "priority_index": 0
      }
    }
  ],
  "total_count": 2
}
```

### 2. Get Upcoming Events (for Timeline)

Optimized endpoint for the UpcomingEventsCard component.

```
GET /api/v1/sites/{site_id}/events/upcoming
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hours_ahead` | int | `24` | How far ahead to look (hours, max: 168) |
| `limit` | int | `15` | Maximum number of events to return (max: 50) |

#### Response

Same structure as `/events/` but only returns `pending` and `in-progress` events within the time window.

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
  description: string | null;
  scheduled_time: string;  // ISO 8601 datetime with timezone
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  equipment: string[];     // List of device_ids affected
  source: string;          // e.g., 'chillerplantschedule', 'controlschedule'
  payload: object;         // Action-specific data (chiller_id, group_equipment, etc.)
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
    `${API_BASE_URL}/sites/${siteId}/events/upcoming?limit=15`
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

## Data Source

### MongoDB Collection

Events are stored in MongoDB (per-site instance):
- **Database**: `control`
- **Collection**: `action_event`

Each site has its own MongoDB instance configured in `config/sites.yaml`.

### MongoDB Document Structure

```javascript
{
  "_id": "AUTO-SCHEDULE-2025Dec28-1700-Priority3-stop_chiller_sequence",
  "action_id": "AUTO-SCHEDULE-2025Dec28-1700-Priority3-stop_chiller_sequence",
  "action_type": "stop_chiller_sequence",
  "description": null,
  "payload": {
    "chiller_id": "chiller_4",
    "group_equipment": ["pchp_4", "cdp_4"],
    "priority_index": 2,
    "post_circulation": true,
    "post_circulation_delay": 1800
  },
  "scheduled_time": ISODate("2025-12-28T10:00:00.000Z"),
  "source": "chillerplantschedule",
  "status": "pending",
  "target_agent": "chillersequence"
}
```

## Notes

- All times are returned in ISO 8601 format with site's local timezone
- Equipment IDs match device_ids from realtime data (e.g., `chiller_1`, `pchp_2`)
- Events are created by `alto-cero-automation-backend` (chiller sequences, schedules)
- The API is **READ-ONLY** - it only reads from MongoDB, never writes
