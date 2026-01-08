"""AI-powered analytics API endpoints.

Provides natural language chart generation and template management.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.analytics.service import get_analytics_service
from app.analytics.templates.manager import get_template_manager
from app.config import get_site_by_id

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Schemas


class ChartGenerationRequest(BaseModel):
    """Request to generate a chart from natural language."""

    prompt: str = Field(..., description="Natural language description of desired chart")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Optional parameter overrides"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Show me the plant efficiency trend for the last 2 weeks",
                "parameters": {"resolution": "1h"},
            }
        }


class TemplateChartRequest(BaseModel):
    """Request to generate chart from a template."""

    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Template parameters"
    )


class ChartGenerationResponse(BaseModel):
    """Response containing generated chart."""

    chart_id: Optional[str] = None
    plotly_spec: Optional[Dict[str, Any]] = None
    template_used: Optional[str] = None
    template_match_confidence: Optional[float] = None
    data_sources: List[str] = Field(default_factory=list)
    query_summary: str = ""
    message: str = ""
    suggestions: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class TemplateListItem(BaseModel):
    """Template summary for listing."""

    template_id: str
    title: str
    description: str
    category: str
    created_by: str
    usage_count: int
    tags: List[str]


class TemplateListResponse(BaseModel):
    """List of templates."""

    templates: List[TemplateListItem]
    total_count: int
    builtin_count: int
    custom_count: int


class CreateTemplateRequest(BaseModel):
    """Request to create a new template."""

    template_id: str = Field(..., description="Unique template ID (snake_case)")
    title: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="What this chart shows")
    trigger_phrases: List[str] = Field(..., description="Phrases that trigger this template")
    category: str = Field(..., description="Template category")
    data_config: Dict[str, Any] = Field(..., description="Data query configuration")
    chart_config: Dict[str, Any] = Field(..., description="Chart configuration")


# Endpoints


@router.post(
    "/chart",
    response_model=ChartGenerationResponse,
    summary="Generate chart from prompt",
    description="Generate a chart from a natural language description. Will try template matching first, then AI generation.",
)
async def generate_chart(
    site_id: str = Path(..., description="Site identifier"),
    request: ChartGenerationRequest = ...,
) -> ChartGenerationResponse:
    """Generate a chart from natural language prompt."""
    logger.info(f"[AI-ANALYTICS] === Chart Generation Request ===")
    logger.info(f"[AI-ANALYTICS] Site: {site_id}")
    logger.info(f"[AI-ANALYTICS] Prompt: {request.prompt}")
    logger.info(f"[AI-ANALYTICS] Parameters: {request.parameters}")

    site = get_site_by_id(site_id)
    if site is None:
        logger.error(f"[AI-ANALYTICS] Site not found: {site_id}")
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")

    logger.info(f"[AI-ANALYTICS] Site found: {site.site_name}")

    service = get_analytics_service(site_id, site.site_name)
    logger.info(f"[AI-ANALYTICS] Calling analytics service...")

    result = await service.generate_chart(
        prompt=request.prompt,
        parameters=request.parameters,
    )

    logger.info(f"[AI-ANALYTICS] === Result ===")
    logger.info(f"[AI-ANALYTICS] Chart ID: {result.get('chart_id')}")
    logger.info(f"[AI-ANALYTICS] Template used: {result.get('template_used')}")
    logger.info(f"[AI-ANALYTICS] Template confidence: {result.get('template_match_confidence')}")
    logger.info(f"[AI-ANALYTICS] Has plotly_spec: {result.get('plotly_spec') is not None}")
    logger.info(f"[AI-ANALYTICS] Message: {result.get('message')}")
    logger.info(f"[AI-ANALYTICS] Error: {result.get('error')}")

    return ChartGenerationResponse(**result)


@router.post(
    "/chart/stream",
    summary="Generate chart with streaming progress",
    description="Generate a chart with SSE streaming for real-time progress updates.",
)
async def generate_chart_stream(
    site_id: str = Path(..., description="Site identifier"),
    request: ChartGenerationRequest = ...,
) -> StreamingResponse:
    """Generate a chart with streaming progress updates."""

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for chart generation progress."""
        try:
            # Send start event
            yield f"data: {json.dumps({'event': 'start', 'message': 'Starting chart generation...'})}\n\n"

            site = get_site_by_id(site_id)
            if site is None:
                yield f"data: {json.dumps({'event': 'error', 'message': f'Site {site_id} not found'})}\n\n"
                return

            yield f"data: {json.dumps({'event': 'progress', 'message': f'Site: {site.site_name}', 'step': 1})}\n\n"

            service = get_analytics_service(site_id, site.site_name)

            # Check for template match
            yield f"data: {json.dumps({'event': 'progress', 'message': 'Checking templates...', 'step': 2})}\n\n"

            # Generate chart
            yield f"data: {json.dumps({'event': 'progress', 'message': 'Generating chart...', 'step': 3})}\n\n"

            result = await service.generate_chart(
                prompt=request.prompt,
                parameters=request.parameters,
            )

            if result.get("template_used"):
                template_name = result["template_used"]
                yield f"data: {json.dumps({'event': 'progress', 'message': f'Using template: {template_name}', 'step': 4})}\n\n"
            else:
                yield f"data: {json.dumps({'event': 'progress', 'message': 'AI generating chart...', 'step': 4})}\n\n"

            # Send final result
            yield f"data: {json.dumps({'event': 'complete', 'result': result})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/chart/from-template/{template_id}",
    response_model=ChartGenerationResponse,
    summary="Generate chart from template",
    description="Generate a chart using a specific template with parameters.",
)
async def generate_from_template(
    site_id: str = Path(..., description="Site identifier"),
    template_id: str = Path(..., description="Template identifier"),
    request: TemplateChartRequest = ...,
) -> ChartGenerationResponse:
    """Generate a chart from a specific template."""
    site = get_site_by_id(site_id)
    if site is None:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")

    service = get_analytics_service(site_id, site.site_name)
    result = await service.generate_from_template(
        template_id=template_id,
        parameters=request.parameters,
    )

    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    return ChartGenerationResponse(**result)


@router.get(
    "/templates",
    response_model=TemplateListResponse,
    summary="List templates",
    description="List available chart templates for this site.",
)
async def list_templates(
    site_id: str = Path(..., description="Site identifier"),
    category: Optional[str] = Query(None, description="Filter by category"),
    include_builtin: bool = Query(True, description="Include builtin templates"),
    include_custom: bool = Query(True, description="Include custom templates"),
) -> TemplateListResponse:
    """List available chart templates."""
    manager = get_template_manager()

    templates = manager.list_templates(
        site_id=site_id,
        category=category,
        include_builtin=include_builtin,
        include_custom=include_custom,
    )

    builtin_count = sum(1 for t in templates if t.created_by == "system")
    custom_count = len(templates) - builtin_count

    return TemplateListResponse(
        templates=[
            TemplateListItem(
                template_id=t.template_id,
                title=t.title,
                description=t.description,
                category=t.category,
                created_by=t.created_by,
                usage_count=t.usage_count,
                tags=t.tags,
            )
            for t in templates
        ],
        total_count=len(templates),
        builtin_count=builtin_count,
        custom_count=custom_count,
    )


@router.get(
    "/templates/{template_id}",
    summary="Get template details",
    description="Get full details of a specific template.",
)
async def get_template(
    site_id: str = Path(..., description="Site identifier"),
    template_id: str = Path(..., description="Template identifier"),
) -> Dict[str, Any]:
    """Get template details."""
    manager = get_template_manager()
    template = manager.get_template(template_id, site_id)

    if template is None:
        raise HTTPException(
            status_code=404, detail=f"Template '{template_id}' not found"
        )

    return template.model_dump(mode="json")


@router.post(
    "/templates",
    summary="Create template",
    description="Create a new custom template for this site.",
)
async def create_template(
    site_id: str = Path(..., description="Site identifier"),
    request: CreateTemplateRequest = ...,
) -> Dict[str, Any]:
    """Create a new custom template."""
    from app.llm.tools.template_tools import execute_save_chart_template

    result = await execute_save_chart_template(
        site_id=site_id,
        template_id=request.template_id,
        title=request.title,
        description=request.description,
        trigger_phrases=request.trigger_phrases,
        category=request.category,
        data_config=request.data_config,
        chart_config=request.chart_config,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create template"))

    return result


@router.delete(
    "/templates/{template_id}",
    summary="Delete template",
    description="Delete a custom template. Builtin templates cannot be deleted.",
)
async def delete_template(
    site_id: str = Path(..., description="Site identifier"),
    template_id: str = Path(..., description="Template identifier"),
) -> Dict[str, str]:
    """Delete a custom template."""
    manager = get_template_manager()

    # Check if template exists and is custom
    template = manager.get_template(template_id, site_id)
    if template is None:
        raise HTTPException(
            status_code=404, detail=f"Template '{template_id}' not found"
        )

    if template.created_by == "system":
        raise HTTPException(
            status_code=403, detail="Cannot delete builtin templates"
        )

    success = manager.delete_template(template_id, site_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete template")

    return {"message": f"Template '{template_id}' deleted successfully"}
