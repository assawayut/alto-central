"""LLM Chat API endpoints (STUB - Phase 3+).

These endpoints will provide natural language interaction for HVAC insights.
Currently returns mock/placeholder responses.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Path, Query
from pydantic import BaseModel, Field

router = APIRouter()


class ChatMessage(BaseModel):
    """A chat message."""

    role: str = Field(..., description="Message role (user, assistant)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request body."""

    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for context")


class ChatResponse(BaseModel):
    """Chat response."""

    session_id: str
    message: str
    sources: Optional[List[Dict]] = None
    actions_taken: Optional[List[str]] = None


# Mock responses for different types of questions
MOCK_RESPONSES = {
    "efficiency": """Based on current data, your plant is operating at 0.746 kW/RT efficiency.

**Analysis:**
- This is slightly above the optimal range of 0.60-0.70 kW/RT
- Chiller 2 is running at 92% load with 0.78 kW/RT efficiency
- Cooling tower approach is 8°F (target: 6°F)

**Recommendations:**
1. Consider staging down Chiller 2 if load permits
2. Increase cooling tower fan speed to reduce approach
3. Check condenser water flow rate on Chiller 2""",
    "chiller": """Here's the current status of your chillers:

| Chiller | Status | Load | Power | Efficiency |
|---------|--------|------|-------|------------|
| CH-1 | Running | 85% | 95 kW | 0.72 kW/RT |
| CH-2 | Running | 92% | 91 kW | 0.78 kW/RT |
| CH-3 | Standby | - | - | - |
| CH-4 | Standby | - | - | - |

Total plant load: 250 RT
Total power: 186 kW""",
    "default": """I'm your HVAC assistant. I can help you with:

- **Real-time monitoring**: "What's the current plant efficiency?"
- **Equipment status**: "Show me chiller status"
- **Fault analysis**: "Why is chiller 2 using more power?"
- **Recommendations**: "How can we reduce energy usage?"
- **Historical analysis**: "Compare today's performance to yesterday"

What would you like to know?""",
}


def get_mock_response(message: str) -> str:
    """Get a mock response based on message content."""
    message_lower = message.lower()

    if any(word in message_lower for word in ["efficiency", "kw/rt", "performance"]):
        return MOCK_RESPONSES["efficiency"]
    elif any(word in message_lower for word in ["chiller", "ch-", "compressor"]):
        return MOCK_RESPONSES["chiller"]
    else:
        return MOCK_RESPONSES["default"]


@router.post(
    "/message",
    response_model=ChatResponse,
    summary="Send a chat message",
    description="[STUB] Send a message to the LLM assistant.",
)
async def send_message(
    site_id: str = Path(..., description="Site identifier"),
    request: ChatRequest = ...,
) -> ChatResponse:
    """Send a message to the LLM assistant.

    The assistant can query plant data, run analyses, and provide recommendations.
    """
    session_id = request.session_id or str(uuid4())
    response_text = get_mock_response(request.message)

    return ChatResponse(
        session_id=session_id,
        message=response_text,
        sources=[
            {"type": "realtime_data", "device": "plant"},
            {"type": "realtime_data", "device": "chiller_1"},
            {"type": "realtime_data", "device": "chiller_2"},
        ],
        actions_taken=["Queried real-time data", "Analyzed chiller performance"],
    )


@router.get(
    "/sessions",
    summary="List chat sessions",
    description="[STUB] Returns list of chat sessions for the site.",
)
async def list_sessions(
    site_id: str = Path(..., description="Site identifier"),
    limit: int = Query(10, description="Maximum sessions to return"),
) -> Dict:
    """List recent chat sessions."""
    return {
        "site_id": site_id,
        "sessions": [
            {
                "session_id": "sess_001",
                "created_at": "2024-01-15T08:00:00Z",
                "last_message_at": "2024-01-15T08:15:00Z",
                "message_count": 5,
                "summary": "Discussed plant efficiency optimization",
            },
            {
                "session_id": "sess_002",
                "created_at": "2024-01-14T14:30:00Z",
                "last_message_at": "2024-01-14T14:45:00Z",
                "message_count": 3,
                "summary": "Chiller fault analysis",
            },
        ],
        "_stub": True,
    }


@router.get(
    "/sessions/{session_id}/history",
    summary="Get session history",
    description="[STUB] Returns message history for a session.",
)
async def get_session_history(
    site_id: str = Path(..., description="Site identifier"),
    session_id: str = Path(..., description="Session identifier"),
) -> Dict:
    """Get chat history for a session."""
    return {
        "site_id": site_id,
        "session_id": session_id,
        "messages": [
            {
                "role": "user",
                "content": "What's the current plant efficiency?",
                "timestamp": "2024-01-15T08:00:00Z",
            },
            {
                "role": "assistant",
                "content": MOCK_RESPONSES["efficiency"],
                "timestamp": "2024-01-15T08:00:02Z",
            },
            {
                "role": "user",
                "content": "Show me the chiller status",
                "timestamp": "2024-01-15T08:05:00Z",
            },
            {
                "role": "assistant",
                "content": MOCK_RESPONSES["chiller"],
                "timestamp": "2024-01-15T08:05:01Z",
            },
        ],
        "_stub": True,
    }


@router.post(
    "/analyze",
    summary="Run analysis with LLM",
    description="[STUB] Run a specific analysis using the LLM.",
)
async def run_analysis(
    site_id: str = Path(..., description="Site identifier"),
    analysis_type: str = Query(
        ...,
        description="Type of analysis (efficiency, faults, comparison, forecast)",
    ),
) -> Dict:
    """Run a specific analysis using the LLM.

    Available analysis types:
    - efficiency: Analyze plant efficiency
    - faults: Analyze current faults and root causes
    - comparison: Compare to previous period
    - forecast: Forecast next 24 hours
    """
    analyses = {
        "efficiency": {
            "title": "Plant Efficiency Analysis",
            "summary": "Plant operating at 0.746 kW/RT, 10% above optimal",
            "findings": [
                "Chiller 2 part-load efficiency is degraded",
                "Cooling tower approach 2°F above design",
                "CHW delta-T is 8°F (target: 10°F)",
            ],
            "recommendations": [
                "Optimize chiller staging",
                "Increase CT fan speed",
                "Check CHW flow balance",
            ],
        },
        "faults": {
            "title": "Fault Analysis",
            "summary": "3 active faults detected",
            "findings": [
                "Low CHW delta-T indicates bypassing or over-pumping",
                "CT vibration may indicate bearing wear",
                "AHU-1 SAT deviation from setpoint",
            ],
            "root_causes": [
                "Possible failed 3-way valve on AHU-3",
                "CT-2 bearing wear (scheduled maintenance overdue)",
            ],
        },
    }

    return {
        "site_id": site_id,
        "analysis_type": analysis_type,
        "result": analyses.get(
            analysis_type,
            {"summary": f"Analysis type '{analysis_type}' not implemented"},
        ),
        "generated_at": datetime.utcnow().isoformat(),
        "_stub": True,
    }
