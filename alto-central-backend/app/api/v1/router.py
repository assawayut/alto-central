"""API v1 router - aggregates all endpoints."""

from fastapi import APIRouter

from app.api.v1 import sites, realtime, ontology, timeseries, energy, afdd, ml, optimization, chat, analytics

api_router = APIRouter()

# Sites list
api_router.include_router(
    sites.router,
    prefix="/sites",
    tags=["Sites"],
)

# Phase 1 - Core APIs
api_router.include_router(
    realtime.router,
    prefix="/sites/{site_id}/realtime",
    tags=["Real-Time Data"],
)

api_router.include_router(
    ontology.router,
    prefix="/sites/{site_id}/ontology",
    tags=["Ontology"],
)

api_router.include_router(
    timeseries.router,
    prefix="/sites/{site_id}/timeseries",
    tags=["Timeseries"],
)

api_router.include_router(
    energy.router,
    prefix="/sites/{site_id}/energy",
    tags=["Energy"],
)

api_router.include_router(
    afdd.router,
    prefix="/sites/{site_id}/afdd",
    tags=["AFDD Alerts"],
)

api_router.include_router(
    analytics.router,
    prefix="/sites/{site_id}/analytics",
    tags=["Analytics"],
)

# Phase 2+ - ML, Optimization, LLM (stubs)
api_router.include_router(
    ml.router,
    prefix="/ml",
    tags=["Machine Learning"],
)

api_router.include_router(
    optimization.router,
    prefix="/sites/{site_id}/optimization",
    tags=["Optimization"],
)

api_router.include_router(
    chat.router,
    prefix="/sites/{site_id}/chat",
    tags=["LLM Chat"],
)
