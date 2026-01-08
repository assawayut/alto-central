"""Tool registry for AI-powered analytics.

Combines all tool definitions and executors for use with Claude.
"""

from typing import Any, Callable, Dict, List

from app.llm.tools.data_tools import (
    DATA_TOOLS,
    TOOL_EXECUTORS as DATA_EXECUTORS,
    execute_query_timeseries,
    execute_query_realtime,
    execute_aggregate_data,
    execute_list_available_datapoints,
)
from app.llm.tools.chart_tools import (
    CHART_TOOLS,
    TOOL_EXECUTORS as CHART_EXECUTORS,
    ASYNC_TOOL_EXECUTORS as CHART_ASYNC_EXECUTORS,
    execute_create_line_chart,
    execute_create_scatter_chart,
    execute_create_bar_chart,
    execute_create_multi_axis_chart,
    execute_query_and_chart,
)
from app.llm.tools.template_tools import (
    TEMPLATE_TOOLS,
    TOOL_EXECUTORS as TEMPLATE_EXECUTORS,
    execute_save_chart_template,
    execute_list_templates,
    execute_get_template,
)

# Combine all tool definitions
ALL_TOOLS: List[Dict[str, Any]] = DATA_TOOLS + CHART_TOOLS + TEMPLATE_TOOLS

# Combine all executors
ALL_EXECUTORS: Dict[str, Callable] = {
    **DATA_EXECUTORS,
    **CHART_EXECUTORS,
    **CHART_ASYNC_EXECUTORS,
    **TEMPLATE_EXECUTORS,
}


async def execute_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    site_id: str,
) -> Any:
    """Execute a tool by name with the given input.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool
        site_id: Site context for the tool

    Returns:
        Tool execution result
    """
    executor = ALL_EXECUTORS.get(tool_name)
    if executor is None:
        return {"error": f"Unknown tool: {tool_name}"}

    # Add site_id to input for tools that need it
    if tool_name in DATA_EXECUTORS:
        # Data tools need site_id as first arg
        return await executor(site_id, **tool_input)
    elif tool_name in TEMPLATE_EXECUTORS:
        # Template tools need site_id as first arg
        return await executor(site_id, **tool_input)
    elif tool_name in CHART_ASYNC_EXECUTORS:
        # Async chart tools (like query_and_chart) need site_id
        return await executor(site_id, **tool_input)
    else:
        # Sync chart tools don't need site_id
        return executor(**tool_input)


def get_tool_definitions(
    include_data: bool = True,
    include_chart: bool = True,
    include_template: bool = True,
) -> List[Dict[str, Any]]:
    """Get tool definitions for Claude API.

    Args:
        include_data: Include data fetching tools
        include_chart: Include chart creation tools
        include_template: Include template management tools

    Returns:
        List of tool definitions in Claude API format
    """
    tools = []
    if include_data:
        tools.extend(DATA_TOOLS)
    if include_chart:
        tools.extend(CHART_TOOLS)
    if include_template:
        tools.extend(TEMPLATE_TOOLS)
    return tools


__all__ = [
    "ALL_TOOLS",
    "ALL_EXECUTORS",
    "execute_tool",
    "get_tool_definitions",
    # Data tools
    "DATA_TOOLS",
    "execute_query_timeseries",
    "execute_query_realtime",
    "execute_aggregate_data",
    "execute_list_available_datapoints",
    # Chart tools
    "CHART_TOOLS",
    "CHART_ASYNC_EXECUTORS",
    "execute_create_line_chart",
    "execute_create_scatter_chart",
    "execute_create_bar_chart",
    "execute_create_multi_axis_chart",
    "execute_query_and_chart",
    # Template tools
    "TEMPLATE_TOOLS",
    "execute_save_chart_template",
    "execute_list_templates",
    "execute_get_template",
]
