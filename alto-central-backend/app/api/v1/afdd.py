"""AFDD (Automated Fault Detection and Diagnostics) API endpoints.

These endpoints provide fault detection alerts.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Path, Query

from app.models.schemas.alerts import (
    Alert,
    AlertSeverityCounts,
    AlertSummary,
    AlertResponse,
    AlertSummaryResponse,
)

router = APIRouter()


def get_mock_alerts(site_id: str) -> List[Alert]:
    """Return mock alerts for testing."""
    return [
        Alert(
            id="alert_001",
            fault_name="Low Delta-T on Chilled Water Loop",
            fault_code="CHW_DT_001",
            category="water-side",
            severity="warning",
            device_id="chilled_water_loop",
            is_active=True,
            active_at=datetime(2024, 1, 15, 8, 30),
            message="Chilled water delta-T is below optimal range (< 8°F)",
        ),
        Alert(
            id="alert_002",
            fault_name="Cooling Tower Fan Vibration",
            fault_code="CT_VIB_001",
            category="water-side",
            severity="info",
            device_id="ct_2",
            is_active=True,
            active_at=datetime(2024, 1, 15, 10, 15),
            message="Elevated vibration detected on cooling tower 2 fan",
        ),
        Alert(
            id="alert_003",
            fault_name="AHU Supply Air Temperature Deviation",
            fault_code="AHU_SAT_001",
            category="air-side",
            severity="info",
            device_id="ahu_1",
            is_active=True,
            active_at=datetime(2024, 1, 15, 9, 45),
            message="Supply air temperature deviating from setpoint",
        ),
    ]


@router.get(
    "/alerts",
    response_model=AlertResponse,
    summary="Get active alerts",
    description="Returns all active AFDD alerts for a site.",
)
async def get_alerts(
    site_id: str = Path(..., description="Site identifier"),
    category: Optional[str] = Query(
        None,
        description="Filter by category (water-side, air-side, electrical)",
    ),
    severity: Optional[str] = Query(
        None,
        description="Filter by severity (critical, warning, info)",
    ),
    is_active: bool = Query(True, description="Filter by active status"),
) -> AlertResponse:
    """Get AFDD alerts for a site."""
    alerts = get_mock_alerts(site_id)

    # Apply filters
    if category:
        alerts = [a for a in alerts if a.category == category]
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    if is_active is not None:
        alerts = [a for a in alerts if a.is_active == is_active]

    return AlertResponse(
        site_id=site_id,
        alerts=alerts,
        total_count=len(alerts),
    )


@router.get(
    "/alerts/summary",
    response_model=AlertSummaryResponse,
    summary="Get alert summary",
    description="Returns a summary of active alerts by category and severity.",
)
async def get_alert_summary(
    site_id: str = Path(..., description="Site identifier"),
) -> AlertSummaryResponse:
    """Get alert summary grouped by category and severity."""
    alerts = get_mock_alerts(site_id)
    active_alerts = [a for a in alerts if a.is_active]

    # Count by category and severity
    summary = AlertSummary(
        water_side=AlertSeverityCounts(critical=0, warning=0, info=0),
        air_side=AlertSeverityCounts(critical=0, warning=0, info=0),
        electrical=AlertSeverityCounts(critical=0, warning=0, info=0),
    )

    for alert in active_alerts:
        if alert.category == "water-side":
            if alert.severity == "critical":
                summary.water_side.critical += 1
            elif alert.severity == "warning":
                summary.water_side.warning += 1
            else:
                summary.water_side.info += 1
        elif alert.category == "air-side":
            if alert.severity == "critical":
                summary.air_side.critical += 1
            elif alert.severity == "warning":
                summary.air_side.warning += 1
            else:
                summary.air_side.info += 1
        elif alert.category == "electrical":
            if alert.severity == "critical":
                summary.electrical.critical += 1
            elif alert.severity == "warning":
                summary.electrical.warning += 1
            else:
                summary.electrical.info += 1

    return AlertSummaryResponse(
        site_id=site_id,
        summary=summary,
        total_active=len(active_alerts),
    )


@router.post(
    "/alerts/{alert_id}/acknowledge",
    summary="Acknowledge an alert",
    description="Mark an alert as acknowledged.",
)
async def acknowledge_alert(
    site_id: str = Path(..., description="Site identifier"),
    alert_id: str = Path(..., description="Alert identifier"),
) -> dict:
    """Acknowledge an alert."""
    # This would update the alert in the database
    return {
        "status": "acknowledged",
        "alert_id": alert_id,
        "acknowledged_at": datetime.utcnow().isoformat(),
    }
