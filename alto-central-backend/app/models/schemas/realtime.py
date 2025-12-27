"""Schemas for real-time data endpoints."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DatapointValue(BaseModel):
    """A single datapoint value with timestamp."""

    value: float = Field(..., description="The datapoint value")
    updated_at: datetime = Field(..., description="When the value was last updated")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    is_stale: bool = Field(False, description="Whether the value is stale")


class DeviceDataResponse(BaseModel):
    """Response containing all datapoints for a single device."""

    device_id: str = Field(..., description="Device identifier")
    datapoints: Dict[str, DatapointValue] = Field(
        ..., description="Map of datapoint name to value"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "chiller_1",
                "datapoints": {
                    "status_read": {"value": 1, "updated_at": "2024-01-15T10:30:00Z"},
                    "power": {"value": 95.5, "updated_at": "2024-01-15T10:30:00Z"},
                    "efficiency": {"value": 0.72, "updated_at": "2024-01-15T10:30:00Z"},
                },
            }
        }


class RealtimeDataResponse(BaseModel):
    """Response containing real-time data for all devices at a site."""

    site_id: str = Field(..., description="Site identifier")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp",
    )
    devices: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Nested map: device_id -> datapoint -> {value, updated_at}",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "site_id": "jwmb",
                "timestamp": "2024-01-15T10:30:00Z",
                "devices": {
                    "plant": {
                        "power": {"value": 186.5, "updated_at": "2024-01-15T10:30:00Z"},
                        "cooling_rate": {"value": 250.0, "updated_at": "2024-01-15T10:30:00Z"},
                    },
                    "chiller_1": {
                        "status_read": {"value": 1, "updated_at": "2024-01-15T10:30:00Z"},
                        "power": {"value": 95.5, "updated_at": "2024-01-15T10:30:00Z"},
                    },
                },
            }
        }
