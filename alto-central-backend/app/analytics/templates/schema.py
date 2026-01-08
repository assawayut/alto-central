"""Chart template Pydantic schemas.

Defines the structure for reusable chart templates that can be:
- Pre-defined (builtin templates)
- AI-generated (custom templates)
- User-created
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TriggerMatching(BaseModel):
    """Template matching configuration for natural language prompts."""

    trigger_phrases: List[str] = Field(
        ..., description="Phrases that trigger this template"
    )
    required_keywords: List[List[str]] = Field(
        default_factory=list,
        description="At least one keyword from each group required",
    )
    excluded_keywords: List[str] = Field(
        default_factory=list, description="Keywords that exclude this template"
    )
    confidence_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum confidence to match"
    )


class DerivedField(BaseModel):
    """Calculated field from raw data."""

    name: str = Field(..., description="Name of derived field")
    formula: str = Field(..., description="Formula expression (e.g., 'power / cooling_rate')")
    unit: Optional[str] = Field(None, description="Unit of measurement")


class DataQuery(BaseModel):
    """Data query specification for a template."""

    query_id: str = Field(..., description="Unique identifier for this query")
    device_id: str = Field(..., description="Device to query (e.g., 'plant', 'chiller_1')")
    datapoints: List[str] = Field(..., description="Datapoints to fetch")
    derived: List[DerivedField] = Field(
        default_factory=list, description="Calculated fields"
    )


class DataFilter(BaseModel):
    """Filter to apply to queried data."""

    field: str = Field(..., description="Field name to filter")
    operator: Literal["eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in"] = Field(
        ..., description="Comparison operator"
    )
    value: Any = Field(..., description="Value to compare against")


class TimeRangeConfig(BaseModel):
    """Time range configuration."""

    type: Literal["relative", "absolute"] = Field(
        default="relative", description="Time range type"
    )
    value: str = Field(
        default="30d",
        description="Relative: '7d', '30d', '1h'. Absolute: ISO timestamp",
    )


class OutlierFilterConfig(BaseModel):
    """Outlier filtering configuration."""

    enabled: bool = Field(default=True, description="Enable outlier filtering")
    method: Literal["iqr", "hvac_bounds", "both"] = Field(
        default="both", description="Filtering method"
    )
    iqr_multiplier: float = Field(
        default=1.5, ge=1.0, le=3.0, description="IQR multiplier for outlier detection"
    )
    min_load: Optional[float] = Field(
        None, description="Minimum cooling_rate to include (filters low-load noise)"
    )


class DataConfig(BaseModel):
    """Complete data source configuration for a template."""

    source: Literal["timescale", "supabase", "both"] = Field(
        default="timescale", description="Data source to use"
    )
    queries: List[DataQuery] = Field(..., description="Data queries to execute")
    default_time_range: TimeRangeConfig = Field(
        default_factory=lambda: TimeRangeConfig(type="relative", value="30d")
    )
    resampling: Optional[str] = Field(
        None, description="Resampling interval (e.g., '1h', '15m')"
    )
    filters: List[DataFilter] = Field(
        default_factory=list, description="Filters to apply"
    )
    outlier_filter: OutlierFilterConfig = Field(
        default_factory=OutlierFilterConfig,
        description="Outlier filtering configuration",
    )


class AxisConfig(BaseModel):
    """Axis configuration for charts."""

    title: str = Field(..., description="Axis title")
    field: str = Field(..., description="Data field for this axis")
    type: Optional[Literal["linear", "log", "date", "category"]] = Field(
        None, description="Axis type"
    )
    range: Optional[List[float]] = Field(None, description="Fixed axis range [min, max]")


class MarkerConfig(BaseModel):
    """Marker configuration for scatter/line traces."""

    size: int = Field(default=6, description="Marker size")
    opacity: float = Field(default=0.7, ge=0.0, le=1.0)
    color: Optional[str] = Field(None, description="Fixed color or field name")
    color_field: Optional[str] = Field(None, description="Field to use for color scale")
    colorscale: Optional[str] = Field(None, description="Plotly colorscale name")


class LineConfig(BaseModel):
    """Line configuration for line traces."""

    width: int = Field(default=2)
    dash: Optional[Literal["solid", "dot", "dash", "dashdot"]] = Field(None)
    color: Optional[str] = Field(None)


class ChartTrace(BaseModel):
    """Single trace configuration for a chart."""

    name: str = Field(..., description="Trace name (legend label)")
    type: Literal["scatter", "line", "bar", "box", "heatmap"] = Field(
        ..., description="Trace type"
    )
    mode: Optional[str] = Field(
        None, description="Mode for scatter: 'lines', 'markers', 'lines+markers'"
    )
    x_field: str = Field(..., description="Data field for x-axis")
    y_field: str = Field(..., description="Data field for y-axis")
    marker: Optional[MarkerConfig] = Field(None)
    line: Optional[LineConfig] = Field(None)
    yaxis: Optional[str] = Field(None, description="Secondary axis: 'y2'")


class ChartLayout(BaseModel):
    """Chart layout configuration."""

    title: str = Field(..., description="Chart title")
    xaxis: AxisConfig = Field(..., description="X-axis configuration")
    yaxis: AxisConfig = Field(..., description="Y-axis configuration")
    yaxis2: Optional[AxisConfig] = Field(None, description="Secondary Y-axis")
    legend: Optional[Dict[str, Any]] = Field(None, description="Legend configuration")
    height: Optional[int] = Field(None, description="Chart height in pixels")
    width: Optional[int] = Field(None, description="Chart width in pixels")


class ChartConfig(BaseModel):
    """Complete chart configuration."""

    type: Literal["line", "scatter", "bar", "heatmap", "box", "multi"] = Field(
        ..., description="Primary chart type"
    )
    layout: ChartLayout = Field(..., description="Layout configuration")
    traces: List[ChartTrace] = Field(..., description="Data traces")
    shapes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Plotly shapes (reference lines, etc.)"
    )
    annotations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Chart annotations"
    )


class TemplateParameter(BaseModel):
    """User-configurable parameter for a template."""

    name: str = Field(..., description="Parameter name")
    type: Literal["string", "number", "date_range", "enum", "boolean", "device"] = Field(
        ..., description="Parameter type"
    )
    default: Any = Field(..., description="Default value")
    description: str = Field(..., description="User-facing description")
    options: Optional[List[str]] = Field(None, description="Options for enum type")
    required: bool = Field(default=False)


class TemplateMetadata(BaseModel):
    """Template metadata for display and categorization."""

    title: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="What this chart shows")
    category: Literal[
        "performance", "energy", "equipment", "comparison", "forecast", "custom"
    ] = Field(..., description="Template category")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    hvac_context: Literal["water", "air", "all"] = Field(
        default="all", description="Applicable HVAC system type"
    )


class ChartTemplate(BaseModel):
    """Complete chart template schema.

    Templates define reusable chart configurations that can be:
    - Matched by natural language prompts
    - Parameterized for different date ranges, devices, etc.
    - Saved/updated by the AI
    """

    template_id: str = Field(..., description="Unique template identifier (snake_case)")
    version: str = Field(default="1.0.0", description="Semantic version")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Literal["system", "ai", "user"] = Field(
        default="system", description="Template creator"
    )

    matching: TriggerMatching = Field(..., description="Matching configuration")
    metadata: TemplateMetadata = Field(..., description="Display metadata")
    data: DataConfig = Field(..., description="Data query configuration")
    chart: ChartConfig = Field(..., description="Chart configuration")
    parameters: List[TemplateParameter] = Field(
        default_factory=list, description="Customizable parameters"
    )

    # Usage tracking
    usage_count: int = Field(default=0, description="Times this template was used")
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    last_used: Optional[datetime] = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "plant_efficiency_vs_load",
                "version": "1.0.0",
                "created_by": "system",
                "matching": {
                    "trigger_phrases": [
                        "plant efficiency",
                        "kw per ton",
                        "efficiency vs load",
                    ],
                    "confidence_threshold": 0.7,
                },
                "metadata": {
                    "title": "Plant Efficiency vs Cooling Load",
                    "description": "Scatter plot of kW/RT vs cooling load",
                    "category": "performance",
                    "tags": ["efficiency", "scatter", "plant"],
                },
                "data": {
                    "source": "timescale",
                    "queries": [
                        {
                            "query_id": "plant_data",
                            "device_id": "plant",
                            "datapoints": ["power", "cooling_rate"],
                            "derived": [
                                {
                                    "name": "efficiency",
                                    "formula": "power / cooling_rate",
                                    "unit": "kW/RT",
                                }
                            ],
                        }
                    ],
                    "default_time_range": {"type": "relative", "value": "30d"},
                    "resampling": "1h",
                },
                "chart": {
                    "type": "scatter",
                    "layout": {
                        "title": "Plant Efficiency vs Cooling Load",
                        "xaxis": {"title": "Cooling Load (RT)", "field": "cooling_rate"},
                        "yaxis": {"title": "Efficiency (kW/RT)", "field": "efficiency"},
                    },
                    "traces": [
                        {
                            "name": "Operating Points",
                            "type": "scatter",
                            "mode": "markers",
                            "x_field": "cooling_rate",
                            "y_field": "efficiency",
                        }
                    ],
                },
            }
        }


class TemplateListItem(BaseModel):
    """Summary of a template for listing."""

    template_id: str
    title: str
    description: str
    category: str
    created_by: str
    version: str
    usage_count: int
    tags: List[str]
