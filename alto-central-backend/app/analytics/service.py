"""Main analytics service orchestrator.

Handles chart generation from natural language prompts,
template matching, and AI-driven analysis.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.llm.client import get_anthropic_client
from app.llm.prompts import get_system_prompt
from app.llm.tools import execute_tool, get_tool_definitions
from app.analytics.templates.matcher import get_template_matcher
from app.analytics.templates.manager import get_template_manager
from app.analytics.templates.schema import ChartTemplate
from app.analytics.charts.plotly_builder import PlotlyBuilder

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Main service for AI-powered analytics."""

    def __init__(self, site_id: str, site_name: Optional[str] = None):
        """Initialize analytics service for a site.

        Args:
            site_id: Site identifier
            site_name: Optional site name for prompts
        """
        self.site_id = site_id
        self.site_name = site_name
        self._client = get_anthropic_client()
        self._matcher = get_template_matcher()
        self._manager = get_template_manager()

    async def generate_chart(
        self,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        use_templates: bool = True,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        """Generate a chart from a natural language prompt.

        Args:
            prompt: User's natural language description
            parameters: Optional parameter overrides
            use_templates: Whether to try template matching first
            use_ai: Whether to use AI for custom chart generation

        Returns:
            Dict with chart_id, plotly_spec, message, etc.
        """
        logger.info(f"[SERVICE] generate_chart called")
        logger.info(f"[SERVICE] prompt: {prompt}")
        logger.info(f"[SERVICE] parameters: {parameters}")
        logger.info(f"[SERVICE] use_templates: {use_templates}, use_ai: {use_ai}")

        chart_id = str(uuid.uuid4())[:8]
        result = {
            "chart_id": chart_id,
            "plotly_spec": None,
            "template_used": None,
            "template_match_confidence": None,
            "data_sources": [],
            "query_summary": "",
            "message": "",
            "suggestions": [],
        }

        # Try template matching first
        if use_templates:
            logger.info(f"[SERVICE] Attempting template matching...")
            match = self._matcher.find_match(prompt, self.site_id)
            if match:
                template, confidence = match
                logger.info(f"[SERVICE] Template matched: {template.template_id} (confidence: {confidence:.2f})")

                try:
                    chart_result = await self._generate_from_template(
                        template, parameters
                    )
                    result.update(chart_result)
                    result["template_used"] = template.template_id
                    result["template_match_confidence"] = confidence
                    result["message"] = f"Generated chart using '{template.metadata.title}' template."

                    # Record usage
                    self._manager.record_usage(template.template_id, self.site_id)

                    logger.info(f"[SERVICE] Template generation successful")
                    return result
                except Exception as e:
                    logger.warning(f"[SERVICE] Template execution failed: {e}, falling back to AI")
            else:
                logger.info(f"[SERVICE] No template matched")

        # Use AI for custom chart generation
        logger.info(f"[SERVICE] Checking AI availability...")
        logger.info(f"[SERVICE] AI configured: {self._client.is_configured}")

        if use_ai and self._client.is_configured:
            logger.info(f"[SERVICE] Starting AI generation...")
            try:
                ai_result = await self._generate_with_ai(prompt)
                result.update(ai_result)
                logger.info(f"[SERVICE] AI generation completed")
                logger.info(f"[SERVICE] AI result has plotly_spec: {ai_result.get('plotly_spec') is not None}")
                return result
            except Exception as e:
                logger.error(f"[SERVICE] AI generation failed: {e}", exc_info=True)
                result["message"] = f"Failed to generate chart: {e}"
                return result
        else:
            logger.warning(f"[SERVICE] AI not available (use_ai={use_ai}, configured={self._client.is_configured})")

        result["message"] = "No template matched and AI is not available."
        return result

    async def _generate_from_template(
        self,
        template: ChartTemplate,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a chart from a template.

        Args:
            template: Chart template to use
            parameters: Optional parameter overrides

        Returns:
            Dict with plotly_spec and metadata
        """
        params = parameters or {}
        data_sources = []
        all_data = []

        # Execute data queries
        for query in template.data.queries:
            device_id = query.device_id

            # Substitute parameters in device_id
            if "{" in device_id:
                for param_name, param_value in params.items():
                    device_id = device_id.replace(f"{{{param_name}}}", str(param_value))

            # Determine time range
            time_range = template.data.default_time_range
            if "date_range" in params:
                time_range_val = params["date_range"]
            else:
                time_range_val = time_range.value

            # Import and execute query
            from app.llm.tools.data_tools import execute_query_timeseries

            query_result = await execute_query_timeseries(
                site_id=self.site_id,
                device_id=device_id,
                datapoints=query.datapoints,
                start_time=time_range_val,
                end_time="now",
                resample=template.data.resampling,
            )

            if "error" not in query_result:
                data_sources.append(f"timescale:{device_id}")
                all_data.extend(query_result.get("data", []))

                # Calculate derived fields
                if query.derived:
                    for record in all_data:
                        for derived in query.derived:
                            try:
                                # Simple formula evaluation
                                formula = derived.formula
                                for dp in query.datapoints:
                                    if dp in record:
                                        formula = formula.replace(dp, str(record[dp]))
                                record[derived.name] = eval(formula)
                            except Exception:
                                record[derived.name] = None

        # Apply filters
        if template.data.filters:
            filtered_data = []
            for record in all_data:
                include = True
                for f in template.data.filters:
                    val = record.get(f.field)
                    if val is None:
                        include = False
                        break
                    if f.operator == "gte" and val < f.value:
                        include = False
                    elif f.operator == "gt" and val <= f.value:
                        include = False
                    elif f.operator == "lte" and val > f.value:
                        include = False
                    elif f.operator == "lt" and val >= f.value:
                        include = False
                if include:
                    filtered_data.append(record)
            all_data = filtered_data

        # Build chart using template config
        chart_type = template.chart.type
        layout = template.chart.layout

        if chart_type == "scatter":
            trace = template.chart.traces[0] if template.chart.traces else None
            plotly_spec = PlotlyBuilder.scatter_chart(
                data=all_data,
                x_field=trace.x_field if trace else layout.xaxis.field,
                y_field=trace.y_field if trace else layout.yaxis.field,
                title=layout.title,
                x_label=layout.xaxis.title,
                y_label=layout.yaxis.title,
            )
        elif chart_type == "line":
            y_fields = [t.y_field for t in template.chart.traces]
            plotly_spec = PlotlyBuilder.line_chart(
                data=all_data,
                x_field=layout.xaxis.field,
                y_fields=y_fields,
                title=layout.title,
                x_label=layout.xaxis.title,
                y_label=layout.yaxis.title,
            )
        elif chart_type == "bar":
            trace = template.chart.traces[0] if template.chart.traces else None
            plotly_spec = PlotlyBuilder.bar_chart(
                data=all_data,
                x_field=trace.x_field if trace else layout.xaxis.field,
                y_field=trace.y_field if trace else layout.yaxis.field,
                title=layout.title,
                x_label=layout.xaxis.title,
                y_label=layout.yaxis.title,
            )
        elif chart_type == "multi":
            y1_fields = [t.y_field for t in template.chart.traces if not t.yaxis]
            y2_fields = [t.y_field for t in template.chart.traces if t.yaxis == "y2"]
            plotly_spec = PlotlyBuilder.multi_axis_chart(
                data=all_data,
                x_field=layout.xaxis.field,
                y1_fields=y1_fields,
                y2_fields=y2_fields,
                title=layout.title,
                x_label=layout.xaxis.title,
                y1_label=layout.yaxis.title,
                y2_label=layout.yaxis2.title if layout.yaxis2 else "Value",
            )
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        return {
            "plotly_spec": plotly_spec,
            "data_sources": data_sources,
            "query_summary": f"Queried {len(all_data)} data points",
        }

    async def _generate_with_ai(self, prompt: str) -> Dict[str, Any]:
        """Generate a chart using AI with tool calling.

        Args:
            prompt: User's natural language prompt

        Returns:
            Dict with plotly_spec and metadata
        """
        logger.info(f"[AI] Starting AI generation for prompt: {prompt}")

        system_prompt = get_system_prompt(site_name=self.site_name)
        tools = get_tool_definitions()

        logger.info(f"[AI] Loaded {len(tools)} tools")
        logger.info(f"[AI] Tools: {[t['name'] for t in tools]}")

        # Create tool executor that includes site_id
        async def tool_executor(tool_name: str, tool_input: Dict) -> Any:
            logger.info(f"[AI] Executing tool: {tool_name}")
            logger.info(f"[AI] Tool input: {tool_input}")
            result = await execute_tool(tool_name, tool_input, self.site_id)
            logger.info(f"[AI] Tool result keys: {result.keys() if isinstance(result, dict) else type(result)}")
            return result

        messages = [{"role": "user", "content": prompt}]

        logger.info(f"[AI] Calling Claude with tools...")
        result = await self._client.chat_with_tools(
            messages=messages,
            system=system_prompt,
            tools=tools,
            tool_executor=tool_executor,
            max_iterations=10,
        )

        logger.info(f"[AI] Claude response received")
        logger.info(f"[AI] Stop reason: {result.get('stop_reason')}")
        logger.info(f"[AI] Tool calls count: {len(result.get('tool_calls', []))}")

        # Extract chart spec from tool calls
        plotly_spec = None
        data_sources = []
        query_summary_parts = []

        for i, call in enumerate(result.get("tool_calls", [])):
            logger.info(f"[AI] Tool call {i+1}: {call.get('tool')} - success: {call.get('success')}")
            if call.get("success"):
                tool = call.get("tool", "")
                result_data = call.get("result", {})

                # Handle query_and_chart (combined tool)
                if tool == "query_and_chart":
                    if result_data.get("plotly_spec"):
                        plotly_spec = result_data["plotly_spec"]
                        logger.info(f"[AI] Got plotly_spec from query_and_chart")
                    summary = result_data.get("data_summary", {})
                    devices = summary.get("devices", [])
                    total_points = summary.get("total_points", 0)
                    data_sources.extend([f"timescale:{d}" for d in devices])
                    query_summary_parts.append(f"{', '.join(devices)}: {total_points} points")
                    logger.info(f"[AI] query_and_chart: {devices} returned {total_points} points")

                # Handle regular query tools
                elif tool.startswith("query_"):
                    device_id = call.get("input", {}).get("device_id", "unknown")
                    row_count = result_data.get("row_count", 0)
                    data_sources.append(f"timescale:{device_id}")
                    query_summary_parts.append(f"{device_id}: {row_count} rows")
                    logger.info(f"[AI] Query result: {device_id} returned {row_count} rows")

                # Handle chart creation tools
                elif tool.startswith("create_") and result_data.get("plotly_spec"):
                    plotly_spec = result_data["plotly_spec"]
                    logger.info(f"[AI] Got plotly_spec from {tool}")
            else:
                logger.warning(f"[AI] Tool call failed: {call.get('error')}")

        logger.info(f"[AI] Final message: {result.get('final_message', '')[:200]}...")

        return {
            "plotly_spec": plotly_spec,
            "data_sources": data_sources,
            "query_summary": ", ".join(query_summary_parts),
            "message": result.get("final_message", ""),
        }

    async def generate_from_template(
        self,
        template_id: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a chart directly from a template ID.

        Args:
            template_id: Template identifier
            parameters: Optional parameter overrides

        Returns:
            Dict with chart_id, plotly_spec, etc.
        """
        template = self._manager.get_template(template_id, self.site_id)
        if template is None:
            return {
                "chart_id": None,
                "error": f"Template '{template_id}' not found",
            }

        chart_id = str(uuid.uuid4())[:8]

        try:
            result = await self._generate_from_template(template, parameters)
            self._manager.record_usage(template_id, self.site_id)

            return {
                "chart_id": chart_id,
                "template_used": template_id,
                "message": f"Generated chart using '{template.metadata.title}' template.",
                **result,
            }
        except Exception as e:
            logger.error(f"Template generation failed: {e}")
            return {
                "chart_id": chart_id,
                "error": str(e),
            }

    def list_templates(
        self,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List available templates.

        Args:
            category: Optional category filter

        Returns:
            List of template summaries
        """
        templates = self._manager.list_templates(
            site_id=self.site_id,
            category=category,
        )

        return [
            {
                "template_id": t.template_id,
                "title": t.title,
                "description": t.description,
                "category": t.category,
                "created_by": t.created_by,
                "usage_count": t.usage_count,
                "tags": t.tags,
            }
            for t in templates
        ]


def get_analytics_service(
    site_id: str,
    site_name: Optional[str] = None,
) -> AnalyticsService:
    """Get an analytics service for a site.

    Note: Creates a new instance each time (not singleton)
    because it's site-specific.
    """
    return AnalyticsService(site_id, site_name)
