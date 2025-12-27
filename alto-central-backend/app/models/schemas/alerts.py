"""Schemas for AFDD alerts endpoints."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Alert(BaseModel):
    """A single AFDD alert."""

    id: str = Field(..., description="Alert identifier")
    fault_name: str = Field(..., description="Name of the fault")
    fault_code: Optional[str] = Field(None, description="Fault code")
    category: str = Field(..., description="Alert category (water-side, air-side, electrical)")
    severity: str = Field(..., description="Severity level (critical, warning, info)")
    device_id: Optional[str] = Field(None, description="Related device")
    is_active: bool = Field(True, description="Whether alert is currently active")
    active_at: datetime = Field(..., description="When the alert became active")
    resolved_at: Optional[datetime] = Field(None, description="When the alert was resolved")
    message: Optional[str] = Field(None, description="Alert message/description")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "alert_123",
                "fault_name": "Chiller Power Mismatch",
                "fault_code": "CH_PWR_001",
                "category": "water-side",
                "severity": "warning",
                "device_id": "chiller_1",
                "is_active": True,
                "active_at": "2024-01-15T08:30:00Z",
                "message": "Chiller 1 power reading differs from expected value",
            }
        }


class AlertSeverityCounts(BaseModel):
    """Count of alerts by severity."""

    critical: int = Field(0, description="Critical alert count")
    warning: int = Field(0, description="Warning alert count")
    info: int = Field(0, description="Info alert count")


class AlertSummary(BaseModel):
    """Summary of alerts by category."""

    water_side: AlertSeverityCounts = Field(
        default_factory=AlertSeverityCounts,
        alias="water-side",
    )
    air_side: AlertSeverityCounts = Field(
        default_factory=AlertSeverityCounts,
        alias="air-side",
    )
    electrical: AlertSeverityCounts = Field(
        default_factory=AlertSeverityCounts,
    )

    class Config:
        populate_by_name = True


class AlertResponse(BaseModel):
    """Response containing alerts for a site."""

    site_id: str
    alerts: List[Alert]
    total_count: int


class AlertSummaryResponse(BaseModel):
    """Response containing alert summary."""

    site_id: str
    summary: AlertSummary
    total_active: int = Field(..., description="Total active alerts")

    class Config:
        json_schema_extra = {
            "example": {
                "site_id": "jwmb",
                "total_active": 3,
                "summary": {
                    "water-side": {"critical": 0, "warning": 1, "info": 0},
                    "air-side": {"critical": 0, "warning": 0, "info": 2},
                    "electrical": {"critical": 0, "warning": 0, "info": 0},
                },
            }
        }
