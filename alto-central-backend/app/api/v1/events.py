"""Action Events API endpoints.

Provides endpoints for retrieving action events from MongoDB.
Events include scheduled maintenance, chiller sequences, and alerts.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Path, Query

from app.db.connections import get_mongodb
from app.core import get_site_timezone

router = APIRouter()


def format_event(event: Dict[str, Any], site_tz) -> Dict[str, Any]:
    """Format a MongoDB event document for API response.

    Converts MongoDB document to the API response format defined in
    docs/UPCOMING_EVENTS_API.md
    """
    # Get scheduled time and convert to site timezone
    scheduled_time = event.get("scheduled_time")
    if isinstance(scheduled_time, datetime):
        scheduled_time_local = scheduled_time.astimezone(site_tz)
        scheduled_time_str = scheduled_time_local.isoformat()
    else:
        scheduled_time_str = str(scheduled_time) if scheduled_time else None

    # Extract equipment from payload
    equipment = []
    payload = event.get("payload", {})
    if payload:
        # For chiller sequences
        if payload.get("chiller_id"):
            equipment.append(payload["chiller_id"])
        if payload.get("group_equipment"):
            equipment.extend(payload["group_equipment"])
        # For schedule actions
        if payload.get("device_datapoint_pair_list"):
            for pair in payload["device_datapoint_pair_list"]:
                if isinstance(pair, list) and len(pair) > 0:
                    equipment.append(pair[0])

    # Map action_type to event_type
    action_type = event.get("action_type", "")
    event_type = action_type  # Use as-is for now

    # Generate title based on action type
    title = event.get("description") or _generate_title(action_type, payload)

    return {
        "event_id": event.get("action_id"),
        "event_type": event_type,
        "title": title,
        "description": event.get("description"),
        "scheduled_time": scheduled_time_str,
        "status": event.get("status", "pending"),
        "equipment": list(set(equipment)),  # Remove duplicates
        "source": event.get("source"),
        "payload": payload,
    }


def _generate_title(action_type: str, payload: Dict[str, Any]) -> str:
    """Generate a human-readable title for an action event."""
    if action_type == "start_chiller_sequence":
        chiller_id = payload.get("chiller_id", "")
        if chiller_id:
            return f"Start {chiller_id.upper().replace('_', '-')}"
        return "Start Chiller Sequence"

    if action_type == "stop_chiller_sequence":
        chiller_id = payload.get("chiller_id", "")
        if chiller_id:
            return f"Stop {chiller_id.upper().replace('_', '-')}"
        return "Stop Chiller Sequence"

    if action_type == "schedule":
        return "Scheduled Control Action"

    return action_type.replace("_", " ").title()


@router.get(
    "/",
    summary="Get action events",
    description="Retrieve action events for a site including scheduled, running, and completed events.",
)
async def get_action_events(
    site_id: str = Path(..., description="Site identifier"),
    status: str = Query(
        "all",
        description="Filter by status",
        enum=["all", "pending", "in-progress", "completed", "failed"],
    ),
    limit: int = Query(20, description="Maximum number of events to return", ge=1, le=100),
) -> Dict[str, Any]:
    """Get action events for a site.

    Returns action events from MongoDB including:
    - Chiller start/stop sequences
    - Scheduled control actions
    - Other automation events

    Events are sorted by scheduled_time (ascending).
    """
    # Get site timezone
    site_tz = get_site_timezone(site_id)

    # Get MongoDB connection
    mongodb = await get_mongodb(site_id)

    if not mongodb.is_connected:
        return {
            "site_id": site_id,
            "events": [],
            "total_count": 0,
            "message": "MongoDB not connected",
        }

    # Fetch events
    events = await mongodb.get_action_events(status=status, limit=limit)

    # Format events for response
    formatted_events = [format_event(event, site_tz) for event in events]

    return {
        "site_id": site_id,
        "events": formatted_events,
        "total_count": len(formatted_events),
    }


@router.get(
    "/upcoming",
    summary="Get upcoming events",
    description="Get pending and in-progress events scheduled for the next N hours.",
)
async def get_upcoming_events(
    site_id: str = Path(..., description="Site identifier"),
    hours_ahead: int = Query(24, description="How far ahead to look (hours)", ge=1, le=168),
    limit: int = Query(15, description="Maximum number of events to return", ge=1, le=50),
) -> Dict[str, Any]:
    """Get upcoming events for the timeline display.

    Optimized for the UpcomingEventsCard component.
    Returns only pending and in-progress events within the specified time window.
    """
    # Get site timezone
    site_tz = get_site_timezone(site_id)

    # Get MongoDB connection
    mongodb = await get_mongodb(site_id)

    if not mongodb.is_connected:
        return {
            "site_id": site_id,
            "events": [],
            "total_count": 0,
            "message": "MongoDB not connected",
        }

    # Fetch pending events
    pending_events = await mongodb.get_action_events(status="pending", limit=limit)
    in_progress_events = await mongodb.get_action_events(status="in-progress", limit=limit)

    # Combine and filter by time window
    now = datetime.now(site_tz)
    cutoff = now + timedelta(hours=hours_ahead)

    all_events = pending_events + in_progress_events
    filtered_events = []

    for event in all_events:
        scheduled_time = event.get("scheduled_time")
        if isinstance(scheduled_time, datetime):
            # Make sure it's within the time window
            if scheduled_time <= cutoff:
                filtered_events.append(event)
        else:
            # Include if we can't determine time
            filtered_events.append(event)

    # Sort by scheduled_time
    filtered_events.sort(
        key=lambda e: e.get("scheduled_time") or datetime.max.replace(tzinfo=site_tz)
    )

    # Limit results
    filtered_events = filtered_events[:limit]

    # Format events for response
    formatted_events = [format_event(event, site_tz) for event in filtered_events]

    return {
        "site_id": site_id,
        "events": formatted_events,
        "total_count": len(formatted_events),
    }
