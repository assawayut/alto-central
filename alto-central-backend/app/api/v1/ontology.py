"""Ontology/Equipment API endpoints.

These endpoints provide equipment entity information.
"""

from typing import List, Optional

from fastapi import APIRouter, Path, Query

from app.models.schemas.ontology import OntologyEntity, OntologyResponse

router = APIRouter()

# Mock equipment data (will be replaced with real database queries)
MOCK_EQUIPMENT = {
    "jwmb": [
        OntologyEntity(
            entity_id="chiller_1",
            name="Chiller 1",
            tags={"model": "chiller", "spaceRef": "plant", "manufacturer": "Carrier"},
            metadata={"capacity_tons": 500, "install_date": "2020-01-15"},
        ),
        OntologyEntity(
            entity_id="chiller_2",
            name="Chiller 2",
            tags={"model": "chiller", "spaceRef": "plant", "manufacturer": "Carrier"},
            metadata={"capacity_tons": 500, "install_date": "2020-01-15"},
        ),
        OntologyEntity(
            entity_id="chiller_3",
            name="Chiller 3",
            tags={"model": "chiller", "spaceRef": "plant", "manufacturer": "Trane"},
            metadata={"capacity_tons": 600, "install_date": "2021-06-01"},
        ),
        OntologyEntity(
            entity_id="chiller_4",
            name="Chiller 4",
            tags={"model": "chiller", "spaceRef": "plant", "manufacturer": "Trane"},
            metadata={"capacity_tons": 600, "install_date": "2021-06-01"},
        ),
        OntologyEntity(
            entity_id="pchp_1",
            name="Primary CHW Pump 1",
            tags={"model": "pchp", "spaceRef": "plant"},
            metadata={"power_hp": 50},
        ),
        OntologyEntity(
            entity_id="pchp_2",
            name="Primary CHW Pump 2",
            tags={"model": "pchp", "spaceRef": "plant"},
            metadata={"power_hp": 50},
        ),
        OntologyEntity(
            entity_id="pchp_3",
            name="Primary CHW Pump 3",
            tags={"model": "pchp", "spaceRef": "plant"},
            metadata={"power_hp": 50},
        ),
        OntologyEntity(
            entity_id="pchp_4",
            name="Primary CHW Pump 4",
            tags={"model": "pchp", "spaceRef": "plant"},
            metadata={"power_hp": 50},
        ),
        OntologyEntity(
            entity_id="cdp_1",
            name="Condenser Pump 1",
            tags={"model": "cdp", "spaceRef": "plant"},
            metadata={"power_hp": 40},
        ),
        OntologyEntity(
            entity_id="cdp_2",
            name="Condenser Pump 2",
            tags={"model": "cdp", "spaceRef": "plant"},
            metadata={"power_hp": 40},
        ),
        OntologyEntity(
            entity_id="cdp_3",
            name="Condenser Pump 3",
            tags={"model": "cdp", "spaceRef": "plant"},
            metadata={"power_hp": 40},
        ),
        OntologyEntity(
            entity_id="cdp_4",
            name="Condenser Pump 4",
            tags={"model": "cdp", "spaceRef": "plant"},
            metadata={"power_hp": 40},
        ),
        OntologyEntity(
            entity_id="ct_1",
            name="Cooling Tower 1",
            tags={"model": "ct", "spaceRef": "plant"},
            metadata={"cells": 2},
        ),
        OntologyEntity(
            entity_id="ct_2",
            name="Cooling Tower 2",
            tags={"model": "ct", "spaceRef": "plant"},
            metadata={"cells": 2},
        ),
        OntologyEntity(
            entity_id="ct_3",
            name="Cooling Tower 3",
            tags={"model": "ct", "spaceRef": "plant"},
            metadata={"cells": 2},
        ),
        OntologyEntity(
            entity_id="ct_4",
            name="Cooling Tower 4",
            tags={"model": "ct", "spaceRef": "plant"},
            metadata={"cells": 2},
        ),
    ],
}


def get_mock_equipment(site_id: str) -> List[OntologyEntity]:
    """Get mock equipment for a site."""
    # Return same equipment for all sites (mock)
    return MOCK_EQUIPMENT.get(site_id, MOCK_EQUIPMENT.get("jwmb", []))


@router.get(
    "/entities",
    response_model=OntologyResponse,
    summary="Get all equipment entities",
    description="Returns all equipment entities at a site with optional filtering.",
)
async def get_entities(
    site_id: str = Path(..., description="Site identifier"),
    tag_filter: Optional[str] = Query(
        None,
        description="Filter by tag (e.g., 'model:chiller', 'spaceRef:plant')",
    ),
    model: Optional[str] = Query(
        None,
        description="Filter by equipment model (chiller, pchp, cdp, ct, schp)",
    ),
) -> OntologyResponse:
    """Get all equipment entities at a site."""
    entities = get_mock_equipment(site_id)

    # Apply filters
    if tag_filter:
        key, value = tag_filter.split(":", 1) if ":" in tag_filter else (tag_filter, None)
        if value:
            entities = [e for e in entities if e.tags.get(key) == value]
        else:
            entities = [e for e in entities if key in e.tags]

    if model:
        entities = [e for e in entities if e.tags.get("model") == model]

    return OntologyResponse(
        site_id=site_id,
        entities=entities,
        total_count=len(entities),
    )


@router.get(
    "/entities/{entity_id}",
    response_model=OntologyEntity,
    summary="Get a specific entity",
    description="Returns details for a specific equipment entity.",
)
async def get_entity(
    site_id: str = Path(..., description="Site identifier"),
    entity_id: str = Path(..., description="Entity identifier"),
) -> OntologyEntity:
    """Get a specific equipment entity."""
    entities = get_mock_equipment(site_id)

    for entity in entities:
        if entity.entity_id == entity_id:
            return entity

    # Return a generic entity if not found
    return OntologyEntity(
        entity_id=entity_id,
        name=entity_id.replace("_", " ").title(),
        tags={"model": "unknown"},
    )
