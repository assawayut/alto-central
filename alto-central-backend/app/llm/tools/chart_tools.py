"""Chart creation tools for AI-powered analytics.

These tools allow Claude to generate Plotly chart specifications
from data that has been queried via data tools.
"""

import logging
from typing import Any, Dict, List, Optional

from app.analytics.charts.plotly_builder import PlotlyBuilder

logger = logging.getLogger(__name__)


# Combined query + chart tool (easier to use)
QUERY_AND_CHART_TOOL = {
    "name": "query_and_chart",
    "description": """Query data AND create a chart in one step. This is the PREFERRED tool for most chart requests.
Automatically handles data fetching, filtering, and chart generation.

IMPORTANT: Use the exact device IDs from the user's prompt.
Device patterns: chiller_{N}, cooling_tower_{N}, pchp_{N}, schp_{N}, cdwp_{N}

Examples:
- "compare chiller_1 and chiller_2 efficiency" -> device_ids=["chiller_1", "chiller_2"], metrics=["power", "cooling_rate"], calculate_efficiency=true
- "chiller_3 power trend" -> device_ids=["chiller_3"], metrics=["power"], chart_type="line"
- "plant efficiency" -> device_ids=["plant"], metrics=["power", "cooling_rate"], chart_type="scatter"
- "compare chiller_1 efficiency today vs yesterday" -> device_ids=["chiller_1"], metrics=["efficiency"], compare_periods=["today", "yesterday"]
- "plant efficiency when only chiller_2 running" -> device_ids=["plant"], metrics=["efficiency", "cooling_rate"], filters={"only_running": ["chiller_2"], "not_running": ["chiller_1", "chiller_3"]}
- "plant efficiency when 2 chillers running" -> device_ids=["plant"], metrics=["efficiency", "cooling_rate"], filters={"num_chillers_running": 2}
""",
    "input_schema": {
        "type": "object",
        "properties": {
            "device_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Device IDs to query (e.g., ['chiller_1', 'chiller_2'] or ['plant'])",
            },
            "metrics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Metrics to fetch (e.g., ['power', 'cooling_rate'] for efficiency, or ['efficiency'] directly)",
            },
            "chart_type": {
                "type": "string",
                "enum": ["line", "scatter", "bar"],
                "description": "Chart type: line for trends, scatter for correlations, bar for comparisons",
            },
            "title": {
                "type": "string",
                "description": "Chart title",
            },
            "time_range": {
                "type": "string",
                "description": "Time range: '24h', '7d', '30d', or ISO dates. Ignored if compare_periods is used.",
                "default": "7d",
            },
            "compare_periods": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Compare same metric across time periods. Use ['today', 'yesterday'] or ['2024-01-08', '2024-01-07']. X-axis will be hour of day (0-23).",
            },
            "filters": {
                "type": "object",
                "description": """Filter data by equipment status or conditions. Options:
- only_running: ["chiller_2"] - only include when these devices are running (status_read=1)
- not_running: ["chiller_1", "chiller_3"] - exclude when these devices are running
- num_chillers_running: 2 - only include when exactly N chillers are running
- min_cooling_load: 100 - minimum plant cooling_rate (RT)
- time_of_day: {"start": 8, "end": 18} - filter by hour of day (e.g., working hours)""",
            },
            "x_metric": {
                "type": "string",
                "description": "For scatter plots: which metric for x-axis (default: first metric or 'timestamp' for line)",
            },
            "y_metric": {
                "type": "string",
                "description": "For scatter plots: which metric for y-axis (default: second metric)",
            },
            "calculate_efficiency": {
                "type": "boolean",
                "description": "If true and power+cooling_rate are queried, calculate efficiency (kW/RT)",
                "default": False,
            },
            "resolution": {
                "type": "string",
                "enum": ["15m", "1h", "1d"],
                "description": "Data resolution",
                "default": "1h",
            },
        },
        "required": ["device_ids", "metrics", "chart_type", "title"],
    },
}


# Server-side labeled scatter tool - handles all grouping internally
LABELED_SCATTER_CHART_TOOL = {
    "name": "labeled_scatter_chart",
    "description": """Create a scatter chart with data LABELED/GROUPED by equipment status.
This tool handles ALL data fetching and grouping SERVER-SIDE - much faster than manual queries!

Use this for requests like:
- "plant efficiency vs load labeled by number of chillers running"
- "plant efficiency labeled by which chillers are running"
- "efficiency vs load grouped by chiller combination"

The tool will:
1. Query plant data (efficiency, cooling_rate)
2. Query chiller status for all specified chillers
3. Group data by the labeling criteria
4. Create multi-trace scatter chart with legend

label_by options:
- "chiller_count": Groups by number of chillers running (1, 2, 3, etc.)
- "chiller_combination": Groups by specific chiller combo (CH-1, CH-1+CH-2, etc.)
- "chiller_combination_fixed_count": Groups by combo, filtered to specific count""",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Chart title",
            },
            "time_range": {
                "type": "string",
                "description": "Time range: '24h', '7d', '30d'",
                "default": "7d",
            },
            "x_metric": {
                "type": "string",
                "enum": ["cooling_rate", "power"],
                "description": "X-axis metric (default: cooling_rate)",
                "default": "cooling_rate",
            },
            "y_metric": {
                "type": "string",
                "enum": ["efficiency", "power", "cooling_rate"],
                "description": "Y-axis metric (default: efficiency)",
                "default": "efficiency",
            },
            "label_by": {
                "type": "string",
                "enum": ["chiller_count", "chiller_combination", "chiller_combination_fixed_count"],
                "description": "How to label/group the data points",
            },
            "chiller_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Chiller IDs to check status for (e.g., ['chiller_1', 'chiller_2', 'chiller_3', 'chiller_4'])",
            },
            "fixed_chiller_count": {
                "type": "integer",
                "description": "For 'chiller_combination_fixed_count': only show combinations with exactly N chillers",
            },
            "min_cooling_load": {
                "type": "number",
                "description": "Minimum cooling load to include (default: 50 RT)",
                "default": 50,
            },
            "resolution": {
                "type": "string",
                "enum": ["15m", "1h"],
                "description": "Data resolution",
                "default": "15m",
            },
        },
        "required": ["title", "label_by", "chiller_ids"],
    },
}


# Tool definitions for Claude API
CREATE_LINE_CHART_TOOL = {
    "name": "create_line_chart",
    "description": """Create a line chart for time-series data trends.
Best for showing how values change over time.
Returns a complete Plotly JSON specification.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "data": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Array of data records with timestamp and value fields",
            },
            "x_field": {
                "type": "string",
                "description": "Field name for x-axis (usually 'timestamp')",
            },
            "y_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Field names for y-axis (one per line)",
            },
            "title": {"type": "string", "description": "Chart title"},
            "x_label": {"type": "string", "description": "X-axis label"},
            "y_label": {"type": "string", "description": "Y-axis label"},
            "series_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional names for each series",
            },
        },
        "required": ["data", "x_field", "y_fields", "title"],
    },
}

CREATE_SCATTER_CHART_TOOL = {
    "name": "create_scatter_chart",
    "description": """Create a scatter plot for correlation analysis.
Best for showing relationships between two variables.
Returns a complete Plotly JSON specification.

For coloring by a continuous value (e.g., wetbulb temperature):
- Set color_field to the field name (e.g., "wetbulb_temperature")
- Points will be colored using a gradient (Viridis colorscale)
- A colorbar will show the scale

For multiple labeled traces (e.g., by chiller count), DON'T use this tool.
Instead, query data, group it, and build plotly_spec manually with multiple traces.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "data": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Array of data records. For color_field, include that field in each record.",
            },
            "x_field": {"type": "string", "description": "Field name for x-axis"},
            "y_field": {"type": "string", "description": "Field name for y-axis"},
            "title": {"type": "string", "description": "Chart title"},
            "x_label": {"type": "string", "description": "X-axis label"},
            "y_label": {"type": "string", "description": "Y-axis label"},
            "color_field": {
                "type": "string",
                "description": "Field for color gradient (e.g., 'wetbulb_temperature'). Creates continuous colorscale.",
            },
            "color_label": {
                "type": "string",
                "description": "Label for colorbar (e.g., 'Wetbulb (°F)')",
            },
            "trendline": {
                "type": "boolean",
                "description": "Add linear trendline",
            },
        },
        "required": ["data", "x_field", "y_field", "title", "x_label", "y_label"],
    },
}

CREATE_BAR_CHART_TOOL = {
    "name": "create_bar_chart",
    "description": """Create a bar chart for categorical comparisons.
Best for comparing values across categories or time periods.
Returns a complete Plotly JSON specification.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "data": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Array of data records with category and value",
            },
            "x_field": {"type": "string", "description": "Field name for categories"},
            "y_field": {"type": "string", "description": "Field name for values"},
            "title": {"type": "string", "description": "Chart title"},
            "x_label": {"type": "string", "description": "X-axis label"},
            "y_label": {"type": "string", "description": "Y-axis label"},
            "orientation": {
                "type": "string",
                "enum": ["v", "h"],
                "description": "Bar orientation: v=vertical, h=horizontal",
            },
            "color": {"type": "string", "description": "Bar color (hex or name)"},
        },
        "required": ["data", "x_field", "y_field", "title", "x_label", "y_label"],
    },
}

CREATE_MULTI_TRACE_SCATTER_TOOL = {
    "name": "create_multi_trace_scatter",
    "description": """Create a scatter plot with MULTIPLE labeled traces (groups).
Use this for labeling by categories like:
- Number of chillers running (1 Chiller, 2 Chillers, 3 Chillers)
- Which specific chiller is running (CH-1 only, CH-1+CH-2, etc.)
- Any categorical grouping of data points

Each trace will have a different color and appear in the legend.
Do NOT use this for continuous color scales (use create_scatter_chart with color_field instead).

Example traces input:
[
  {"name": "1 Chiller", "x": [100, 150], "y": [0.8, 0.85], "color": "#1f77b4"},
  {"name": "2 Chillers", "x": [200, 250], "y": [0.7, 0.75], "color": "#ff7f0e"},
  {"name": "3 Chillers", "x": [300, 350], "y": [0.65, 0.68], "color": "#2ca02c"}
]""",
    "input_schema": {
        "type": "object",
        "properties": {
            "traces": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Label for this group (appears in legend)"},
                        "x": {"type": "array", "items": {"type": "number"}, "description": "X values"},
                        "y": {"type": "array", "items": {"type": "number"}, "description": "Y values"},
                        "color": {"type": "string", "description": "Optional hex color (e.g., '#1f77b4')"},
                    },
                    "required": ["name", "x", "y"],
                },
                "description": "Array of trace objects, each representing a labeled group",
            },
            "title": {"type": "string", "description": "Chart title"},
            "x_label": {"type": "string", "description": "X-axis label"},
            "y_label": {"type": "string", "description": "Y-axis label"},
            "marker_size": {"type": "number", "description": "Marker size (default: 6)"},
            "marker_opacity": {"type": "number", "description": "Marker opacity 0-1 (default: 0.7)"},
        },
        "required": ["traces", "title", "x_label", "y_label"],
    },
}

CREATE_3D_SCATTER_CHART_TOOL = {
    "name": "create_3d_scatter_chart",
    "description": """Create a 3D scatter plot to visualize relationships between THREE variables.
Use when user wants to see how 3 metrics relate (e.g., power vs cooling load vs wetbulb).

Example: "3D plot of power, cooling load, and wetbulb temperature"
- x_field: wetbulb_temperature
- y_field: cooling_rate
- z_field: power

Can also color by a 4th variable using color_field.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "data": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Array of data records from query_timeseries",
            },
            "x_field": {"type": "string", "description": "Field for X-axis"},
            "y_field": {"type": "string", "description": "Field for Y-axis"},
            "z_field": {"type": "string", "description": "Field for Z-axis"},
            "title": {"type": "string", "description": "Chart title"},
            "x_label": {"type": "string", "description": "X-axis label"},
            "y_label": {"type": "string", "description": "Y-axis label"},
            "z_label": {"type": "string", "description": "Z-axis label"},
            "color_field": {"type": "string", "description": "Optional field for color gradient"},
            "color_label": {"type": "string", "description": "Label for colorbar"},
        },
        "required": ["data", "x_field", "y_field", "z_field", "title", "x_label", "y_label", "z_label"],
    },
}

CREATE_MULTI_AXIS_CHART_TOOL = {
    "name": "create_multi_axis_chart",
    "description": """Create a chart with two y-axes for different scales.
Use when comparing metrics with different units (e.g., power kW and temperature °F).
Returns a complete Plotly JSON specification.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "data": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Array of data records",
            },
            "x_field": {"type": "string", "description": "Field name for x-axis"},
            "y1_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Fields for primary y-axis (left)",
            },
            "y2_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Fields for secondary y-axis (right)",
            },
            "title": {"type": "string", "description": "Chart title"},
            "x_label": {"type": "string", "description": "X-axis label"},
            "y1_label": {"type": "string", "description": "Primary y-axis label"},
            "y2_label": {"type": "string", "description": "Secondary y-axis label"},
        },
        "required": ["data", "x_field", "y1_fields", "y2_fields", "title", "x_label", "y1_label", "y2_label"],
    },
}


def execute_create_line_chart(
    data: List[Dict[str, Any]],
    x_field: str,
    y_fields: List[str],
    title: str,
    x_label: str = "Time",
    y_label: str = "Value",
    series_names: Optional[List[str]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Execute line chart creation."""
    try:
        spec = PlotlyBuilder.line_chart(
            data=data,
            x_field=x_field,
            y_fields=y_fields,
            title=title,
            x_label=x_label,
            y_label=y_label,
            series_names=series_names,
        )
        return {
            "success": True,
            "chart_type": "line",
            "plotly_spec": spec,
        }
    except Exception as e:
        logger.error(f"create_line_chart failed: {e}")
        return {"success": False, "error": str(e)}


def execute_create_scatter_chart(
    data: List[Dict[str, Any]],
    x_field: str,
    y_field: str,
    title: str,
    x_label: str,
    y_label: str,
    color_field: Optional[str] = None,
    color_label: Optional[str] = None,
    trendline: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """Execute scatter chart creation."""
    try:
        spec = PlotlyBuilder.scatter_chart(
            data=data,
            x_field=x_field,
            y_field=y_field,
            title=title,
            x_label=x_label,
            y_label=y_label,
            color_field=color_field,
            color_label=color_label,
            trendline=trendline,
        )
        return {
            "success": True,
            "chart_type": "scatter",
            "plotly_spec": spec,
        }
    except Exception as e:
        logger.error(f"create_scatter_chart failed: {e}")
        return {"success": False, "error": str(e)}


def execute_create_3d_scatter_chart(
    data: List[Dict[str, Any]],
    x_field: str,
    y_field: str,
    z_field: str,
    title: str,
    x_label: str,
    y_label: str,
    z_label: str,
    color_field: Optional[str] = None,
    color_label: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Execute 3D scatter chart creation."""
    try:
        spec = PlotlyBuilder.scatter_3d_chart(
            data=data,
            x_field=x_field,
            y_field=y_field,
            z_field=z_field,
            title=title,
            x_label=x_label,
            y_label=y_label,
            z_label=z_label,
            color_field=color_field,
            color_label=color_label,
        )
        return {
            "success": True,
            "chart_type": "scatter3d",
            "plotly_spec": spec,
        }
    except Exception as e:
        logger.error(f"create_3d_scatter_chart failed: {e}")
        return {"success": False, "error": str(e)}


def execute_create_bar_chart(
    data: List[Dict[str, Any]],
    x_field: str,
    y_field: str,
    title: str,
    x_label: str,
    y_label: str,
    orientation: str = "v",
    color: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Execute bar chart creation."""
    try:
        spec = PlotlyBuilder.bar_chart(
            data=data,
            x_field=x_field,
            y_field=y_field,
            title=title,
            x_label=x_label,
            y_label=y_label,
            orientation=orientation,
            color=color,
        )
        return {
            "success": True,
            "chart_type": "bar",
            "plotly_spec": spec,
        }
    except Exception as e:
        logger.error(f"create_bar_chart failed: {e}")
        return {"success": False, "error": str(e)}


def execute_create_multi_trace_scatter(
    traces: List[Dict[str, Any]],
    title: str,
    x_label: str,
    y_label: str,
    marker_size: int = 6,
    marker_opacity: float = 0.7,
    **kwargs,
) -> Dict[str, Any]:
    """Execute multi-trace scatter chart creation.

    Each trace represents a labeled group with its own color.
    """
    default_colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
    ]

    try:
        plotly_traces = []
        for i, trace in enumerate(traces):
            color = trace.get("color") or default_colors[i % len(default_colors)]
            plotly_traces.append({
                "type": "scatter",
                "mode": "markers",
                "name": trace["name"],
                "x": trace["x"],
                "y": trace["y"],
                "marker": {
                    "size": marker_size,
                    "opacity": marker_opacity,
                    "color": color,
                },
            })

        spec = {
            "data": plotly_traces,
            "layout": {
                "title": {"text": title, "x": 0.5},
                "xaxis": {
                    "title": x_label,
                    "gridcolor": "rgba(128,128,128,0.2)",
                    "showgrid": True,
                },
                "yaxis": {
                    "title": y_label,
                    "gridcolor": "rgba(128,128,128,0.2)",
                    "showgrid": True,
                },
                "hovermode": "closest",
                "legend": {"orientation": "h", "y": -0.15, "x": 0.5, "xanchor": "center"},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
            },
        }

        return {
            "success": True,
            "chart_type": "multi_trace_scatter",
            "plotly_spec": spec,
        }
    except Exception as e:
        logger.error(f"create_multi_trace_scatter failed: {e}")
        return {"success": False, "error": str(e)}


def execute_create_multi_axis_chart(
    data: List[Dict[str, Any]],
    x_field: str,
    y1_fields: List[str],
    y2_fields: List[str],
    title: str,
    x_label: str,
    y1_label: str,
    y2_label: str,
    **kwargs,
) -> Dict[str, Any]:
    """Execute multi-axis chart creation."""
    try:
        spec = PlotlyBuilder.multi_axis_chart(
            data=data,
            x_field=x_field,
            y1_fields=y1_fields,
            y2_fields=y2_fields,
            title=title,
            x_label=x_label,
            y1_label=y1_label,
            y2_label=y2_label,
        )
        return {
            "success": True,
            "chart_type": "multi_axis",
            "plotly_spec": spec,
        }
    except Exception as e:
        logger.error(f"create_multi_axis_chart failed: {e}")
        return {"success": False, "error": str(e)}


async def execute_labeled_scatter_chart(
    site_id: str,
    title: str,
    label_by: str,
    chiller_ids: List[str],
    time_range: str = "7d",
    x_metric: str = "cooling_rate",
    y_metric: str = "efficiency",
    fixed_chiller_count: Optional[int] = None,
    min_cooling_load: float = 50,
    resolution: str = "15m",
    **kwargs,
) -> Dict[str, Any]:
    """Execute labeled scatter chart with server-side grouping.

    Queries plant data and chiller status, groups by label criteria,
    and returns a multi-trace scatter chart.
    """
    from app.llm.tools.data_tools import execute_query_timeseries, execute_batch_query_timeseries
    from collections import defaultdict
    import asyncio

    logger.info(f"[LABELED_SCATTER] Starting: label_by={label_by}, chillers={chiller_ids}")
    logger.info(f"[LABELED_SCATTER] Time: {time_range}, Resolution: {resolution}")

    try:
        # Handle ISO 8601 interval format (start/end separated by /)
        if "/" in time_range and "T" in time_range:
            parts = time_range.split("/")
            if len(parts) == 2:
                start_time = parts[0]
                end_time = parts[1]
                logger.info(f"[LABELED_SCATTER] Parsed interval: {start_time} to {end_time}")
            else:
                start_time = time_range
                end_time = "now"
        else:
            start_time = time_range
            end_time = "now"

        # Step 1: Query plant data
        plant_result = await execute_query_timeseries(
            site_id=site_id,
            device_id="plant",
            datapoints=["power", "cooling_rate"],
            start_time=start_time,
            end_time=end_time,
            resample=resolution,
            filter_outliers=True,
            min_load=min_cooling_load,
        )

        if "error" in plant_result:
            return {"success": False, "error": f"Failed to query plant data: {plant_result['error']}"}

        plant_data = plant_result.get("data", [])
        logger.info(f"[LABELED_SCATTER] Plant data: {len(plant_data)} rows")

        if not plant_data:
            return {"success": False, "error": "No plant data returned"}

        # Calculate efficiency for plant data
        for record in plant_data:
            power = record.get("power", 0)
            cooling_rate = record.get("cooling_rate", 0)
            if cooling_rate and cooling_rate > 0:
                record["efficiency"] = round(power / cooling_rate, 4)
            else:
                record["efficiency"] = None

        # Step 2: Query chiller status using batch query
        status_result = await execute_batch_query_timeseries(
            site_id=site_id,
            device_ids=chiller_ids,
            datapoints=["status_read"],
            start_time=start_time,
            end_time=end_time,
            resample=resolution,
        )

        if "error" in status_result:
            return {"success": False, "error": f"Failed to query chiller status: {status_result['error']}"}

        status_data = status_result.get("data", [])
        logger.info(f"[LABELED_SCATTER] Chiller status: {len(status_data)} rows")

        # Build status lookup by timestamp -> {device_id: status}
        status_by_ts: Dict[str, Dict[str, float]] = defaultdict(dict)
        for record in status_data:
            ts = record.get("timestamp")
            device_id = record.get("device_id")
            status = record.get("status_read", 0)
            if ts and device_id:
                status_by_ts[ts][device_id] = status if status else 0

        # Step 3: Join plant data with chiller status and compute labels
        grouped_data: Dict[str, List[Dict]] = defaultdict(list)

        for record in plant_data:
            ts = record.get("timestamp")
            x_val = record.get(x_metric)
            y_val = record.get(y_metric)

            if ts is None or x_val is None or y_val is None:
                continue

            # Get chiller statuses for this timestamp
            statuses = status_by_ts.get(ts, {})

            # Determine which chillers are running
            running_chillers = [
                ch for ch in chiller_ids
                if statuses.get(ch, 0) >= 1
            ]
            num_running = len(running_chillers)

            # Skip if no chillers running
            if num_running == 0:
                continue

            # Compute label based on label_by
            if label_by == "chiller_count":
                label = f"{num_running} Chiller{'s' if num_running > 1 else ''}"
            elif label_by == "chiller_combination":
                # Format as "CH-1", "CH-1+CH-2", etc.
                combo = "+".join([
                    f"CH-{ch.split('_')[-1]}" for ch in sorted(running_chillers)
                ])
                label = combo
            elif label_by == "chiller_combination_fixed_count":
                if fixed_chiller_count is not None and num_running != fixed_chiller_count:
                    continue  # Skip if not matching the fixed count
                combo = "+".join([
                    f"CH-{ch.split('_')[-1]}" for ch in sorted(running_chillers)
                ])
                label = combo
            else:
                label = f"{num_running} Chillers"

            grouped_data[label].append({
                "x": x_val,
                "y": y_val,
            })

        logger.info(f"[LABELED_SCATTER] Groups: {list(grouped_data.keys())}")
        for label, points in grouped_data.items():
            logger.info(f"[LABELED_SCATTER]   {label}: {len(points)} points")

        if not grouped_data:
            return {"success": False, "error": "No data after grouping"}

        # Step 4: Build traces for multi-trace scatter
        colors = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
        ]

        # Sort labels for consistent ordering
        if label_by == "chiller_count":
            # Sort numerically by chiller count
            sorted_labels = sorted(grouped_data.keys(), key=lambda x: int(x.split()[0]))
        else:
            # Sort alphabetically
            sorted_labels = sorted(grouped_data.keys())

        traces = []
        for i, label in enumerate(sorted_labels):
            points = grouped_data[label]
            traces.append({
                "type": "scatter",
                "mode": "markers",
                "name": label,
                "x": [p["x"] for p in points],
                "y": [p["y"] for p in points],
                "marker": {
                    "size": 6,
                    "opacity": 0.7,
                    "color": colors[i % len(colors)],
                },
            })

        # Build axis labels
        x_label_map = {
            "cooling_rate": "Cooling Load (RT)",
            "power": "Power (kW)",
        }
        y_label_map = {
            "efficiency": "Efficiency (kW/RT)",
            "power": "Power (kW)",
            "cooling_rate": "Cooling Load (RT)",
        }

        spec = {
            "data": traces,
            "layout": {
                "title": {"text": title, "x": 0.5},
                "xaxis": {
                    "title": x_label_map.get(x_metric, x_metric),
                    "gridcolor": "rgba(128,128,128,0.2)",
                    "showgrid": True,
                },
                "yaxis": {
                    "title": y_label_map.get(y_metric, y_metric),
                    "gridcolor": "rgba(128,128,128,0.2)",
                    "showgrid": True,
                },
                "hovermode": "closest",
                "legend": {"orientation": "h", "y": -0.15, "x": 0.5, "xanchor": "center"},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
            },
        }

        total_points = sum(len(grouped_data[l]) for l in grouped_data)
        logger.info(f"[LABELED_SCATTER] Chart created: {len(traces)} traces, {total_points} points")

        return {
            "success": True,
            "chart_type": "labeled_scatter",
            "plotly_spec": spec,
            "data_summary": {
                "label_by": label_by,
                "groups": list(sorted_labels),
                "total_points": total_points,
                "time_range": time_range,
            },
        }

    except Exception as e:
        logger.error(f"[LABELED_SCATTER] Failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def _execute_period_comparison(
    site_id: str,
    device_ids: List[str],
    metrics: List[str],
    compare_periods: List[str],
    title: str,
    calculate_efficiency: bool = False,
    resolution: str = "1h",
) -> Dict[str, Any]:
    """Execute period comparison chart (e.g., today vs yesterday).

    Creates a line chart where:
    - X-axis: Hour of day (0-23)
    - Y-axis: The metric value
    - Multiple lines: One per period (e.g., "Today", "Yesterday")
    """
    from app.llm.tools.data_tools import execute_query_timeseries
    from app.config import get_site_by_id
    from datetime import datetime

    logger.info(f"[PERIOD_COMPARE] Starting comparison: periods={compare_periods}")

    # Get site timezone
    site = get_site_by_id(site_id)
    site_timezone = site.timezone if site else "Asia/Bangkok"
    logger.info(f"[PERIOD_COMPARE] Using timezone: {site_timezone}")

    traces = []
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    # Determine the metric to plot
    if "efficiency" in metrics:
        y_metric = "efficiency"
    elif calculate_efficiency:
        y_metric = "efficiency"
    else:
        y_metric = metrics[0]

    # Query each period
    for i, period in enumerate(compare_periods):
        start_time, end_time, label = _parse_period_to_dates(period, site_timezone)
        logger.info(f"[PERIOD_COMPARE] Period '{label}': {start_time} to {end_time}")

        period_data = []

        # Query each device for this period
        for device_id in device_ids:
            # Determine which metrics to query
            query_metrics = metrics.copy()
            if calculate_efficiency and "power" not in query_metrics:
                query_metrics.append("power")
            if calculate_efficiency and "cooling_rate" not in query_metrics:
                query_metrics.append("cooling_rate")

            result = await execute_query_timeseries(
                site_id=site_id,
                device_id=device_id,
                datapoints=query_metrics,
                start_time=start_time,
                end_time=end_time,
                resample=resolution,
                filter_outliers=True,
            )

            if "error" in result:
                logger.warning(f"[PERIOD_COMPARE] Query failed for {device_id}: {result['error']}")
                continue

            device_data = result.get("data", [])
            logger.info(f"[PERIOD_COMPARE] {device_id} ({label}): {len(device_data)} rows")

            # Calculate efficiency if needed
            if calculate_efficiency:
                for record in device_data:
                    power = record.get("power", 0)
                    cooling_rate = record.get("cooling_rate", 0)
                    if cooling_rate > 0:
                        record["efficiency"] = round(power / cooling_rate, 3)
                    else:
                        record["efficiency"] = None

            period_data.extend(device_data)

        if not period_data:
            logger.warning(f"[PERIOD_COMPARE] No data for period '{label}'")
            continue

        # Extract hour of day and metric values
        hour_values: Dict[int, List[float]] = {}
        for record in period_data:
            ts_str = record.get("timestamp")
            value = record.get(y_metric)

            if ts_str and value is not None:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    hour = ts.hour
                    if hour not in hour_values:
                        hour_values[hour] = []
                    hour_values[hour].append(value)
                except:
                    pass

        # Average values per hour (in case of multiple data points per hour)
        hours = sorted(hour_values.keys())
        avg_values = [sum(hour_values[h]) / len(hour_values[h]) for h in hours]

        traces.append({
            "type": "scatter",
            "mode": "lines+markers",
            "name": label,
            "x": hours,
            "y": [round(v, 3) for v in avg_values],
            "line": {"width": 2, "color": colors[i % len(colors)]},
            "marker": {"size": 6},
        })

    if not traces:
        return {"success": False, "error": "No data returned for any period"}

    # Build chart spec
    y_label = y_metric.replace("_", " ").title()
    if y_metric == "efficiency":
        y_label = "Efficiency (kW/RT)"

    spec = {
        "data": traces,
        "layout": {
            "title": {"text": title, "x": 0.5},
            "xaxis": {
                "title": "Hour of Day",
                "tickmode": "linear",
                "tick0": 0,
                "dtick": 2,
                "range": [-0.5, 23.5],
            },
            "yaxis": {"title": y_label},
            "hovermode": "x unified",
            "legend": {"orientation": "h", "y": -0.15},
        },
    }

    logger.info(f"[PERIOD_COMPARE] Chart created with {len(traces)} traces")

    return {
        "success": True,
        "chart_type": "period_comparison",
        "plotly_spec": spec,
        "data_summary": {
            "devices": device_ids,
            "periods": compare_periods,
            "metric": y_metric,
        },
    }


def _parse_period_to_dates(period: str, site_timezone: str = "Asia/Bangkok") -> tuple:
    """Convert period name to start/end datetime in site's timezone.

    Returns (start_time, end_time, label) tuple.
    """
    from datetime import datetime, timedelta, timezone
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo

    # Use site's timezone
    try:
        tz = ZoneInfo(site_timezone)
    except:
        tz = timezone.utc
        logger.warning(f"[PERIOD_COMPARE] Invalid timezone '{site_timezone}', using UTC")

    now = datetime.now(tz)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    period_lower = period.lower().strip()

    if period_lower == "today":
        return (today_start.isoformat(), now.isoformat(), "Today")
    elif period_lower == "yesterday":
        yesterday_start = today_start - timedelta(days=1)
        yesterday_end = today_start
        return (yesterday_start.isoformat(), yesterday_end.isoformat(), "Yesterday")
    elif period_lower == "last week" or period_lower == "week ago":
        week_ago_start = today_start - timedelta(days=7)
        week_ago_end = today_start - timedelta(days=6)
        return (week_ago_start.isoformat(), week_ago_end.isoformat(), "Last Week")
    else:
        # Assume it's a date string like "2024-01-08"
        try:
            date = datetime.fromisoformat(period)
            start = date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=tz)
            end = start + timedelta(days=1)
            label = date.strftime("%b %d")
            return (start.isoformat(), end.isoformat(), label)
        except:
            # Fallback - treat as relative
            return (period, "now", period)


async def _apply_filters(
    site_id: str,
    data: List[Dict[str, Any]],
    filters: Dict[str, Any],
    time_range: str,
    resolution: str,
) -> List[Dict[str, Any]]:
    """Apply filters to data based on equipment status and conditions.

    Filters:
    - only_running: list of devices that must be running (status_read >= 1)
    - not_running: list of devices that must NOT be running (status_read < 1)
    - num_chillers_running: exact number of chillers that should be running
    - min_cooling_load: minimum cooling_rate value
    - time_of_day: {"start": 8, "end": 18} - filter by hour
    """
    from app.llm.tools.data_tools import execute_query_timeseries
    from datetime import datetime

    if not data or not filters:
        return data

    logger.info(f"[FILTER] Applying filters: {filters}")

    # Build a map of timestamp -> status for each device we need to check
    status_by_timestamp: Dict[str, Dict[str, int]] = {}

    # Collect all devices we need status for
    devices_to_check = set()
    if "only_running" in filters:
        devices_to_check.update(filters["only_running"])
    if "not_running" in filters:
        devices_to_check.update(filters["not_running"])
    if "num_chillers_running" in filters:
        # Need to check all chillers - assume chiller_1 through chiller_8
        for i in range(1, 9):
            devices_to_check.add(f"chiller_{i}")

    # Query status for each device
    for device_id in devices_to_check:
        result = await execute_query_timeseries(
            site_id=site_id,
            device_id=device_id,
            datapoints=["status_read"],
            start_time=time_range,
            end_time="now",
            resample=resolution,
            filter_outliers=False,
        )

        if "error" not in result:
            for row in result.get("data", []):
                ts = row.get("timestamp")
                status = row.get("status_read", 0)
                if ts:
                    if ts not in status_by_timestamp:
                        status_by_timestamp[ts] = {}
                    status_by_timestamp[ts][device_id] = status if status else 0

    logger.info(f"[FILTER] Loaded status for {len(devices_to_check)} devices, {len(status_by_timestamp)} timestamps")

    # Apply filters
    filtered_data = []
    for record in data:
        ts = record.get("timestamp")
        if not ts:
            continue

        statuses = status_by_timestamp.get(ts, {})
        keep = True

        # Filter: only_running - these devices must have status >= 1
        if "only_running" in filters:
            for device in filters["only_running"]:
                if statuses.get(device, 0) < 1:
                    keep = False
                    break

        # Filter: not_running - these devices must have status < 1
        if keep and "not_running" in filters:
            for device in filters["not_running"]:
                if statuses.get(device, 0) >= 1:
                    keep = False
                    break

        # Filter: num_chillers_running - count running chillers
        if keep and "num_chillers_running" in filters:
            target_count = filters["num_chillers_running"]
            running_count = sum(
                1 for d, s in statuses.items()
                if d.startswith("chiller_") and s >= 1
            )
            if running_count != target_count:
                keep = False

        # Filter: min_cooling_load
        if keep and "min_cooling_load" in filters:
            cooling_rate = record.get("cooling_rate", 0)
            if cooling_rate < filters["min_cooling_load"]:
                keep = False

        # Filter: time_of_day
        if keep and "time_of_day" in filters:
            try:
                ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                hour = ts_dt.hour
                start_hour = filters["time_of_day"].get("start", 0)
                end_hour = filters["time_of_day"].get("end", 24)
                if not (start_hour <= hour < end_hour):
                    keep = False
            except:
                pass

        if keep:
            filtered_data.append(record)

    logger.info(f"[FILTER] Filtered from {len(data)} to {len(filtered_data)} rows")
    return filtered_data


async def execute_query_and_chart(
    site_id: str,
    device_ids: List[str],
    metrics: List[str],
    chart_type: str,
    title: str,
    time_range: str = "7d",
    compare_periods: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    x_metric: Optional[str] = None,
    y_metric: Optional[str] = None,
    calculate_efficiency: bool = False,
    resolution: str = "1h",
    **kwargs,
) -> Dict[str, Any]:
    """Execute combined query and chart creation."""
    from app.llm.tools.data_tools import execute_query_timeseries
    from app.config import get_site_by_id
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    logger.info(f"[QUERY_AND_CHART] Starting: devices={device_ids}, metrics={metrics}, type={chart_type}")
    if compare_periods:
        logger.info(f"[QUERY_AND_CHART] Compare periods: {compare_periods}")
    if filters:
        logger.info(f"[QUERY_AND_CHART] Filters: {filters}")

    try:
        # Handle period comparison mode
        if compare_periods and len(compare_periods) >= 2:
            return await _execute_period_comparison(
                site_id=site_id,
                device_ids=device_ids,
                metrics=metrics,
                compare_periods=compare_periods,
                title=title,
                calculate_efficiency=calculate_efficiency,
                resolution=resolution,
            )

        all_data = []
        data_by_device = {}

        # Query each device
        for device_id in device_ids:
            result = await execute_query_timeseries(
                site_id=site_id,
                device_id=device_id,
                datapoints=metrics,
                start_time=time_range,
                end_time="now",
                resample=resolution,
                filter_outliers=True,
                min_load=50 if calculate_efficiency else None,
            )

            if "error" in result:
                logger.warning(f"[QUERY_AND_CHART] Query failed for {device_id}: {result['error']}")
                continue

            device_data = result.get("data", [])
            logger.info(f"[QUERY_AND_CHART] {device_id}: {len(device_data)} rows")

            # Calculate efficiency if requested
            if calculate_efficiency and "power" in metrics and "cooling_rate" in metrics:
                for record in device_data:
                    power = record.get("power", 0)
                    cooling_rate = record.get("cooling_rate", 0)
                    if cooling_rate > 0:
                        record["efficiency"] = round(power / cooling_rate, 3)
                    else:
                        record["efficiency"] = None

            # Tag data with device for multi-device charts
            for record in device_data:
                record["_device"] = device_id

            data_by_device[device_id] = device_data
            all_data.extend(device_data)

        if not all_data:
            return {"success": False, "error": "No data returned from queries"}

        # Convert timestamps to site's local timezone
        site = get_site_by_id(site_id)
        site_tz = ZoneInfo(site.timezone if site else "Asia/Bangkok")

        def convert_to_local(ts_str: str) -> str:
            """Convert UTC timestamp to site's local timezone."""
            try:
                # Parse the timestamp
                if ts_str.endswith("Z"):
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                elif "+" in ts_str or ts_str.count("-") > 2:
                    dt = datetime.fromisoformat(ts_str)
                else:
                    # Assume UTC if no timezone
                    dt = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)

                # Convert to local timezone
                local_dt = dt.astimezone(site_tz)
                return local_dt.isoformat()
            except Exception:
                return ts_str

        for record in all_data:
            if "timestamp" in record:
                record["timestamp"] = convert_to_local(record["timestamp"])

        # Also update data_by_device for multi-device charts
        for device_id in data_by_device:
            for record in data_by_device[device_id]:
                if "timestamp" in record:
                    record["timestamp"] = convert_to_local(record["timestamp"])

        # Apply filters if specified
        if filters:
            all_data = await _apply_filters(
                site_id=site_id,
                data=all_data,
                filters=filters,
                time_range=time_range,
                resolution=resolution,
            )
            logger.info(f"[QUERY_AND_CHART] After filtering: {len(all_data)} rows")

            if not all_data:
                return {"success": False, "error": "No data after applying filters"}

        logger.info(f"[QUERY_AND_CHART] Total data points: {len(all_data)}")

        # Determine axis fields
        if chart_type == "line":
            x_field = "timestamp"
            if len(device_ids) == 1:
                # Single device: show all metrics
                y_fields = metrics + (["efficiency"] if calculate_efficiency else [])
                spec = PlotlyBuilder.line_chart(
                    data=all_data,
                    x_field=x_field,
                    y_fields=[m for m in y_fields if m in all_data[0]],
                    title=title,
                    x_label="Time",
                    y_label="Value",
                )
            else:
                # Multiple devices: show one metric per device
                primary_metric = y_metric or ("efficiency" if calculate_efficiency else metrics[0])
                traces = []
                for device_id, device_data in data_by_device.items():
                    x_vals = [r.get("timestamp") for r in device_data]
                    y_vals = [r.get(primary_metric) for r in device_data]
                    traces.append({
                        "type": "scatter",
                        "mode": "lines",
                        "name": device_id.replace("_", " ").title(),
                        "x": x_vals,
                        "y": y_vals,
                    })
                spec = {
                    "data": traces,
                    "layout": {
                        "title": {"text": title, "x": 0.5},
                        "xaxis": {"title": "Time", "type": "date"},
                        "yaxis": {"title": primary_metric.replace("_", " ").title()},
                        "hovermode": "x unified",
                        "legend": {"orientation": "h", "y": -0.2},
                    },
                }

        elif chart_type == "scatter":
            x_field = x_metric or ("cooling_rate" if "cooling_rate" in metrics else metrics[0])
            y_field = y_metric or ("efficiency" if calculate_efficiency else metrics[-1])

            if len(device_ids) == 1:
                spec = PlotlyBuilder.scatter_chart(
                    data=all_data,
                    x_field=x_field,
                    y_field=y_field,
                    title=title,
                    x_label=x_field.replace("_", " ").title(),
                    y_label=y_field.replace("_", " ").title(),
                )
            else:
                # Multiple devices: different colors
                traces = []
                colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
                for i, (device_id, device_data) in enumerate(data_by_device.items()):
                    x_vals = [r.get(x_field) for r in device_data if r.get(x_field) is not None and r.get(y_field) is not None]
                    y_vals = [r.get(y_field) for r in device_data if r.get(x_field) is not None and r.get(y_field) is not None]
                    traces.append({
                        "type": "scatter",
                        "mode": "markers",
                        "name": device_id.replace("_", " ").title(),
                        "x": x_vals,
                        "y": y_vals,
                        "marker": {"size": 6, "opacity": 0.6, "color": colors[i % len(colors)]},
                    })
                spec = {
                    "data": traces,
                    "layout": {
                        "title": {"text": title, "x": 0.5},
                        "xaxis": {"title": x_field.replace("_", " ").title()},
                        "yaxis": {"title": y_field.replace("_", " ").title()},
                        "hovermode": "closest",
                        "legend": {"orientation": "h", "y": -0.2},
                    },
                }

        elif chart_type == "bar":
            # Aggregate by device for bar chart
            from statistics import mean
            y_field = y_metric or ("efficiency" if calculate_efficiency else metrics[0])

            bar_data = []
            for device_id, device_data in data_by_device.items():
                values = [r.get(y_field) for r in device_data if r.get(y_field) is not None]
                if values:
                    bar_data.append({
                        "device": device_id.replace("_", " ").title(),
                        "value": round(mean(values), 2),
                    })

            spec = PlotlyBuilder.bar_chart(
                data=bar_data,
                x_field="device",
                y_field="value",
                title=title,
                x_label="Device",
                y_label=y_field.replace("_", " ").title(),
            )

        else:
            return {"success": False, "error": f"Unknown chart type: {chart_type}"}

        logger.info(f"[QUERY_AND_CHART] Chart created successfully")

        return {
            "success": True,
            "chart_type": chart_type,
            "plotly_spec": spec,
            "data_summary": {
                "devices": device_ids,
                "total_points": len(all_data),
                "time_range": time_range,
            },
        }

    except Exception as e:
        logger.error(f"[QUERY_AND_CHART] Failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


# Map tool names to executors
TOOL_EXECUTORS = {
    "create_line_chart": execute_create_line_chart,
    "create_scatter_chart": execute_create_scatter_chart,
    "create_3d_scatter_chart": execute_create_3d_scatter_chart,
    "create_bar_chart": execute_create_bar_chart,
    "create_multi_trace_scatter": execute_create_multi_trace_scatter,
    "create_multi_axis_chart": execute_create_multi_axis_chart,
}

# Async executors (need site_id)
ASYNC_TOOL_EXECUTORS = {
    "query_and_chart": execute_query_and_chart,
    "labeled_scatter_chart": execute_labeled_scatter_chart,
}

# All chart tool definitions
CHART_TOOLS = [
    QUERY_AND_CHART_TOOL,  # Put this first so AI sees it first
    LABELED_SCATTER_CHART_TOOL,  # Server-side grouping for labeled scatter (much faster!)
    CREATE_LINE_CHART_TOOL,
    CREATE_SCATTER_CHART_TOOL,
    CREATE_3D_SCATTER_CHART_TOOL,  # 3D scatter for 3-variable relationships
    CREATE_MULTI_TRACE_SCATTER_TOOL,  # For manual categorical labeling
    CREATE_BAR_CHART_TOOL,
    CREATE_MULTI_AXIS_CHART_TOOL,
]
