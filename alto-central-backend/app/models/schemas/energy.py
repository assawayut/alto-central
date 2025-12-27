"""Schemas for energy data endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class EnergyValues(BaseModel):
    """Energy values breakdown. Values are null when data is not available."""

    total: Optional[float] = Field(None, description="Total energy (kWh)")
    plant: Optional[float] = Field(None, description="Plant energy (kWh)")
    air_side: Optional[float] = Field(None, description="Air-side energy (kWh)")


class EnergyDailyResponse(BaseModel):
    """Response for daily energy comparison."""

    site_id: str = Field(..., description="Site identifier")
    yesterday: EnergyValues = Field(..., description="Yesterday's energy values")
    today: EnergyValues = Field(..., description="Today's energy values (so far)")
    unit: str = Field("kWh", description="Unit of measurement")

    class Config:
        json_schema_extra = {
            "example": {
                "site_id": "jwmb",
                "yesterday": {
                    "total": 12500.0,
                    "plant": 8200.0,
                    "air_side": 4300.0,
                },
                "today": {
                    "total": 10800.0,
                    "plant": 7100.0,
                    "air_side": 3700.0,
                },
                "unit": "kWh",
            }
        }
