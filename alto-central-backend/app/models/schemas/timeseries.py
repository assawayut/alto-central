"""Schemas for timeseries data endpoints."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TimeseriesQuery(BaseModel):
    """Request body for timeseries queries."""

    device_id: str = Field(..., description="Device identifier")
    datapoints: List[str] = Field(..., description="List of datapoint names to query")
    start_timestamp: datetime = Field(..., description="Query start time (ISO 8601)")
    end_timestamp: datetime = Field(..., description="Query end time (ISO 8601)")
    resampling: Optional[str] = Field(
        None,
        description="Resample interval (e.g., '1h', '15m', '1d')",
    )

    @field_validator("datapoints")
    @classmethod
    def validate_datapoints(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one datapoint is required")
        if len(v) > 20:
            raise ValueError("Maximum 20 datapoints per query")
        return v

    @field_validator("resampling")
    @classmethod
    def validate_resampling(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "6h", "1d"]
        if v not in valid_intervals:
            raise ValueError(f"Resampling must be one of: {valid_intervals}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "plant",
                "datapoints": ["power", "cooling_rate"],
                "start_timestamp": "2024-01-14T00:00:00Z",
                "end_timestamp": "2024-01-15T00:00:00Z",
                "resampling": "1h",
            }
        }


class TimeseriesDataPoint(BaseModel):
    """A single timeseries data point."""

    timestamp: datetime
    value: float


class TimeseriesResult(BaseModel):
    """Timeseries data for a single datapoint."""

    device_id: str
    datapoint: str
    values: List[TimeseriesDataPoint]


class TimeseriesResponse(BaseModel):
    """Response containing timeseries query results."""

    site_id: str
    query: TimeseriesQuery
    data: List[TimeseriesResult]

    class Config:
        json_schema_extra = {
            "example": {
                "site_id": "jwmb",
                "query": {
                    "device_id": "plant",
                    "datapoints": ["power"],
                    "start_timestamp": "2024-01-14T00:00:00Z",
                    "end_timestamp": "2024-01-14T03:00:00Z",
                    "resampling": "1h",
                },
                "data": [
                    {
                        "device_id": "plant",
                        "datapoint": "power",
                        "values": [
                            {"timestamp": "2024-01-14T00:00:00Z", "value": 180.5},
                            {"timestamp": "2024-01-14T01:00:00Z", "value": 185.2},
                            {"timestamp": "2024-01-14T02:00:00Z", "value": 178.8},
                        ],
                    }
                ],
            }
        }
