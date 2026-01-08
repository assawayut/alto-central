"""Template management tools for AI-powered analytics.

These tools allow Claude to save, list, and update chart templates.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.analytics.templates.manager import get_template_manager
from app.analytics.templates.schema import (
    ChartTemplate,
    TriggerMatching,
    TemplateMetadata,
    DataConfig,
    DataQuery,
    ChartConfig,
    ChartLayout,
    ChartTrace,
    AxisConfig,
)

logger = logging.getLogger(__name__)


# Tool definitions for Claude API
SAVE_CHART_TEMPLATE_TOOL = {
    "name": "save_chart_template",
    "description": """Save the current chart configuration as a reusable template.
Use when the user explicitly asks to save a chart pattern or when you've
created a useful chart that could be reused. The template will be available
for future requests matching the trigger phrases.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "template_id": {
                "type": "string",
                "description": "Unique identifier (snake_case, e.g., 'chiller_comparison')",
            },
            "title": {"type": "string", "description": "Human-readable title"},
            "description": {"type": "string", "description": "What this chart shows"},
            "trigger_phrases": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Phrases that should trigger this template",
            },
            "category": {
                "type": "string",
                "enum": ["performance", "energy", "equipment", "comparison", "forecast", "custom"],
                "description": "Template category",
            },
            "data_config": {
                "type": "object",
                "description": "Data query configuration (device_id, datapoints, etc.)",
            },
            "chart_config": {
                "type": "object",
                "description": "Chart configuration (type, layout, traces)",
            },
        },
        "required": ["template_id", "title", "description", "trigger_phrases", "category", "data_config", "chart_config"],
    },
}

LIST_TEMPLATES_TOOL = {
    "name": "list_templates",
    "description": """List available chart templates.
Use to find existing templates before creating new charts.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["all", "performance", "energy", "equipment", "comparison", "forecast", "custom"],
                "description": "Filter by category",
            },
        },
        "required": [],
    },
}

GET_TEMPLATE_TOOL = {
    "name": "get_template",
    "description": """Get full details of a specific template.
Use to understand how a template works before using it.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "template_id": {"type": "string", "description": "Template identifier"},
        },
        "required": ["template_id"],
    },
}


async def execute_save_chart_template(
    site_id: str,
    template_id: str,
    title: str,
    description: str,
    trigger_phrases: List[str],
    category: str,
    data_config: Dict[str, Any],
    chart_config: Dict[str, Any],
    **kwargs,
) -> Dict[str, Any]:
    """Execute template save."""
    try:
        manager = get_template_manager()

        # Build the template from provided config
        # Convert data_config dict to DataConfig model
        queries = []
        for q in data_config.get("queries", []):
            queries.append(
                DataQuery(
                    query_id=q.get("query_id", "default"),
                    device_id=q.get("device_id", "plant"),
                    datapoints=q.get("datapoints", []),
                )
            )

        data = DataConfig(
            source=data_config.get("source", "timescale"),
            queries=queries if queries else [DataQuery(query_id="default", device_id="plant", datapoints=["power"])],
            resampling=data_config.get("resampling"),
        )

        # Convert chart_config dict to ChartConfig model
        traces = []
        for t in chart_config.get("traces", []):
            traces.append(
                ChartTrace(
                    name=t.get("name", "Data"),
                    type=t.get("type", "scatter"),
                    mode=t.get("mode"),
                    x_field=t.get("x_field", "timestamp"),
                    y_field=t.get("y_field", "value"),
                )
            )

        layout_config = chart_config.get("layout", {})
        layout = ChartLayout(
            title=layout_config.get("title", title),
            xaxis=AxisConfig(
                title=layout_config.get("xaxis", {}).get("title", "X"),
                field=layout_config.get("xaxis", {}).get("field", "timestamp"),
            ),
            yaxis=AxisConfig(
                title=layout_config.get("yaxis", {}).get("title", "Y"),
                field=layout_config.get("yaxis", {}).get("field", "value"),
            ),
        )

        chart = ChartConfig(
            type=chart_config.get("type", "line"),
            layout=layout,
            traces=traces if traces else [ChartTrace(name="Data", type="scatter", mode="lines", x_field="timestamp", y_field="value")],
        )

        template = ChartTemplate(
            template_id=template_id,
            version="1.0.0",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="ai",
            matching=TriggerMatching(
                trigger_phrases=trigger_phrases,
                confidence_threshold=0.7,
            ),
            metadata=TemplateMetadata(
                title=title,
                description=description,
                category=category,
                tags=[],
            ),
            data=data,
            chart=chart,
        )

        success = manager.save_template(template, site_id, overwrite=False)

        if success:
            return {
                "success": True,
                "message": f"Template '{template_id}' saved successfully",
                "template_id": template_id,
            }
        else:
            return {
                "success": False,
                "error": f"Template '{template_id}' already exists. Use a different ID.",
            }

    except Exception as e:
        logger.error(f"save_chart_template failed: {e}")
        return {"success": False, "error": str(e)}


async def execute_list_templates(
    site_id: str,
    category: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Execute template listing."""
    try:
        manager = get_template_manager()

        cat_filter = None if category == "all" else category
        templates = manager.list_templates(
            site_id=site_id,
            category=cat_filter,
            include_builtin=True,
            include_custom=True,
        )

        return {
            "success": True,
            "count": len(templates),
            "templates": [
                {
                    "template_id": t.template_id,
                    "title": t.title,
                    "description": t.description,
                    "category": t.category,
                    "created_by": t.created_by,
                    "usage_count": t.usage_count,
                }
                for t in templates
            ],
        }

    except Exception as e:
        logger.error(f"list_templates failed: {e}")
        return {"success": False, "error": str(e)}


async def execute_get_template(
    site_id: str,
    template_id: str,
    **kwargs,
) -> Dict[str, Any]:
    """Execute template retrieval."""
    try:
        manager = get_template_manager()
        template = manager.get_template(template_id, site_id)

        if template is None:
            return {
                "success": False,
                "error": f"Template '{template_id}' not found",
            }

        return {
            "success": True,
            "template": template.model_dump(mode="json"),
        }

    except Exception as e:
        logger.error(f"get_template failed: {e}")
        return {"success": False, "error": str(e)}


# Map tool names to executors
TOOL_EXECUTORS = {
    "save_chart_template": execute_save_chart_template,
    "list_templates": execute_list_templates,
    "get_template": execute_get_template,
}

# All template tool definitions
TEMPLATE_TOOLS = [
    SAVE_CHART_TEMPLATE_TOOL,
    LIST_TEMPLATES_TOOL,
    GET_TEMPLATE_TOOL,
]
