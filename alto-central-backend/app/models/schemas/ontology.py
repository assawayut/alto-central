"""Schemas for ontology/equipment endpoints."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class OntologyEntity(BaseModel):
    """An equipment entity in the ontology."""

    entity_id: str = Field(..., description="Unique entity identifier")
    name: str = Field(..., description="Human-readable name")
    tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Entity tags (model, spaceRef, etc.)",
    )
    metadata: Optional[Dict] = Field(
        None,
        description="Additional metadata",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "entity_id": "chiller_1",
                "name": "Chiller 1",
                "tags": {
                    "model": "chiller",
                    "spaceRef": "plant",
                    "manufacturer": "Carrier",
                },
                "metadata": {
                    "capacity_tons": 500,
                    "install_date": "2020-01-15",
                },
            }
        }


class OntologyResponse(BaseModel):
    """Response containing equipment entities for a site."""

    site_id: str = Field(..., description="Site identifier")
    entities: List[OntologyEntity] = Field(..., description="List of entities")
    total_count: int = Field(..., description="Total number of entities")

    class Config:
        json_schema_extra = {
            "example": {
                "site_id": "jwmb",
                "total_count": 3,
                "entities": [
                    {
                        "entity_id": "chiller_1",
                        "name": "Chiller 1",
                        "tags": {"model": "chiller", "spaceRef": "plant"},
                    },
                    {
                        "entity_id": "pchp_1",
                        "name": "Primary CHW Pump 1",
                        "tags": {"model": "pchp", "spaceRef": "plant"},
                    },
                    {
                        "entity_id": "ct_1",
                        "name": "Cooling Tower 1",
                        "tags": {"model": "ct", "spaceRef": "plant"},
                    },
                ],
            }
        }
