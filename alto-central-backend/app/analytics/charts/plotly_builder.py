"""Plotly chart specification builder.

Builds Plotly JSON specs from chart configurations and data.
"""

from typing import Any, Dict, List, Optional


class PlotlyBuilder:
    """Build Plotly JSON specifications for various chart types."""

    # Default Plotly layout settings
    DEFAULT_LAYOUT = {
        "autosize": True,
        "margin": {"l": 60, "r": 30, "t": 50, "b": 60},
        "hovermode": "closest",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, sans-serif"},
        "xaxis": {"gridcolor": "rgba(128,128,128,0.2)", "showgrid": True},
        "yaxis": {"gridcolor": "rgba(128,128,128,0.2)", "showgrid": True},
    }

    # Color palette for traces
    COLOR_PALETTE = [
        "#3498db",  # Blue
        "#e74c3c",  # Red
        "#2ecc71",  # Green
        "#9b59b6",  # Purple
        "#f39c12",  # Orange
        "#1abc9c",  # Teal
        "#e91e63",  # Pink
        "#00bcd4",  # Cyan
    ]

    @classmethod
    def line_chart(
        cls,
        data: List[Dict[str, Any]],
        x_field: str,
        y_fields: List[str],
        title: str,
        x_label: str = "Time",
        y_label: str = "Value",
        series_names: Optional[List[str]] = None,
        line_styles: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Build a line chart specification.

        Args:
            data: List of data records
            x_field: Field name for x-axis (usually 'timestamp')
            y_fields: List of field names for y-axis
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            series_names: Names for each series (defaults to field names)
            line_styles: Optional style overrides per series

        Returns:
            Complete Plotly figure specification
        """
        traces = []
        for i, y_field in enumerate(y_fields):
            x_values = [d.get(x_field) for d in data]
            y_values = [d.get(y_field) for d in data]

            name = series_names[i] if series_names and i < len(series_names) else y_field
            color = cls.COLOR_PALETTE[i % len(cls.COLOR_PALETTE)]

            trace = {
                "type": "scatter",
                "mode": "lines",
                "name": name,
                "x": x_values,
                "y": y_values,
                "line": {"color": color, "width": 2},
            }

            # Apply custom styles
            if line_styles and i < len(line_styles):
                if "color" in line_styles[i]:
                    trace["line"]["color"] = line_styles[i]["color"]
                if "width" in line_styles[i]:
                    trace["line"]["width"] = line_styles[i]["width"]
                if "dash" in line_styles[i]:
                    trace["line"]["dash"] = line_styles[i]["dash"]

            traces.append(trace)

        layout = {
            **cls.DEFAULT_LAYOUT,
            "title": {"text": title, "x": 0.5},
            "xaxis": {
                **cls.DEFAULT_LAYOUT["xaxis"],
                "title": x_label,
                "type": "date" if "timestamp" in x_field.lower() else "-",
            },
            "yaxis": {
                **cls.DEFAULT_LAYOUT["yaxis"],
                "title": y_label,
            },
        }

        return {"data": traces, "layout": layout}

    @classmethod
    def scatter_chart(
        cls,
        data: List[Dict[str, Any]],
        x_field: str,
        y_field: str,
        title: str,
        x_label: str,
        y_label: str,
        color_field: Optional[str] = None,
        color_label: Optional[str] = None,
        size_field: Optional[str] = None,
        marker_size: int = 6,
        marker_opacity: float = 0.7,
        colorscale: str = "Viridis",
        trendline: bool = False,
    ) -> Dict[str, Any]:
        """Build a scatter chart specification.

        Args:
            data: List of data records
            x_field: Field name for x-axis
            y_field: Field name for y-axis
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            color_field: Optional field for color scale
            color_label: Label for colorbar (defaults to color_field name)
            size_field: Optional field for marker size
            marker_size: Default marker size
            marker_opacity: Marker opacity
            colorscale: Plotly colorscale name
            trendline: Whether to add linear trendline

        Returns:
            Complete Plotly figure specification
        """
        x_values = [d.get(x_field) for d in data]
        y_values = [d.get(y_field) for d in data]

        marker = {
            "size": marker_size,
            "opacity": marker_opacity,
        }

        if color_field:
            color_values = [d.get(color_field) for d in data]
            marker["color"] = color_values
            marker["colorscale"] = colorscale
            marker["colorbar"] = {"title": color_label or color_field.replace("_", " ").title()}
        else:
            marker["color"] = cls.COLOR_PALETTE[0]

        if size_field:
            size_values = [d.get(size_field, marker_size) for d in data]
            marker["size"] = size_values
            marker["sizemode"] = "diameter"
            marker["sizeref"] = max(size_values) / 20 if size_values else 1

        traces = [
            {
                "type": "scatter",
                "mode": "markers",
                "name": "Data Points",
                "x": x_values,
                "y": y_values,
                "marker": marker,
            }
        ]

        # Add trendline if requested
        if trendline and x_values and y_values:
            # Simple linear regression
            try:
                import numpy as np

                x_clean = [x for x, y in zip(x_values, y_values) if x is not None and y is not None]
                y_clean = [y for x, y in zip(x_values, y_values) if x is not None and y is not None]

                if len(x_clean) > 1:
                    x_arr = np.array(x_clean, dtype=float)
                    y_arr = np.array(y_clean, dtype=float)
                    coeffs = np.polyfit(x_arr, y_arr, 1)
                    trend_y = np.polyval(coeffs, x_arr)

                    traces.append(
                        {
                            "type": "scatter",
                            "mode": "lines",
                            "name": "Trend",
                            "x": x_clean,
                            "y": trend_y.tolist(),
                            "line": {"color": "#e74c3c", "width": 2, "dash": "dash"},
                        }
                    )
            except Exception:
                pass  # Skip trendline if calculation fails

        layout = {
            **cls.DEFAULT_LAYOUT,
            "title": {"text": title, "x": 0.5},
            "xaxis": {
                **cls.DEFAULT_LAYOUT["xaxis"],
                "title": x_label,
            },
            "yaxis": {
                **cls.DEFAULT_LAYOUT["yaxis"],
                "title": y_label,
            },
        }

        return {"data": traces, "layout": layout}

    @classmethod
    def bar_chart(
        cls,
        data: List[Dict[str, Any]],
        x_field: str,
        y_field: str,
        title: str,
        x_label: str,
        y_label: str,
        orientation: str = "v",
        color: Optional[str] = None,
        bar_width: float = 0.8,
    ) -> Dict[str, Any]:
        """Build a bar chart specification.

        Args:
            data: List of data records
            x_field: Field name for categories
            y_field: Field name for values
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            orientation: 'v' for vertical, 'h' for horizontal
            color: Bar color
            bar_width: Relative bar width

        Returns:
            Complete Plotly figure specification
        """
        x_values = [d.get(x_field) for d in data]
        y_values = [d.get(y_field) for d in data]

        if orientation == "h":
            x_values, y_values = y_values, x_values
            x_label, y_label = y_label, x_label

        traces = [
            {
                "type": "bar",
                "name": y_field,
                "x": x_values,
                "y": y_values,
                "marker": {"color": color or cls.COLOR_PALETTE[2]},
                "width": bar_width,
            }
        ]

        layout = {
            **cls.DEFAULT_LAYOUT,
            "title": {"text": title, "x": 0.5},
            "xaxis": {
                **cls.DEFAULT_LAYOUT["xaxis"],
                "title": x_label,
                "type": "category" if orientation == "v" else "-",
            },
            "yaxis": {
                **cls.DEFAULT_LAYOUT["yaxis"],
                "title": y_label,
            },
            "bargap": 0.1,
        }

        return {"data": traces, "layout": layout}

    @classmethod
    def multi_axis_chart(
        cls,
        data: List[Dict[str, Any]],
        x_field: str,
        y1_fields: List[str],
        y2_fields: List[str],
        title: str,
        x_label: str,
        y1_label: str,
        y2_label: str,
        y1_names: Optional[List[str]] = None,
        y2_names: Optional[List[str]] = None,
        y1_chart_type: str = "line",
        y2_chart_type: str = "line",
    ) -> Dict[str, Any]:
        """Build a dual y-axis chart specification.

        Args:
            data: List of data records
            x_field: Field name for x-axis
            y1_fields: Field names for primary y-axis
            y2_fields: Field names for secondary y-axis
            title: Chart title
            x_label: X-axis label
            y1_label: Primary y-axis label
            y2_label: Secondary y-axis label
            y1_names: Names for primary axis series
            y2_names: Names for secondary axis series
            y1_chart_type: Chart type for primary axis ('line' or 'bar')
            y2_chart_type: Chart type for secondary axis ('line' or 'bar')

        Returns:
            Complete Plotly figure specification
        """
        traces = []
        x_values = [d.get(x_field) for d in data]

        # Primary axis traces
        for i, y_field in enumerate(y1_fields):
            y_values = [d.get(y_field) for d in data]
            name = y1_names[i] if y1_names and i < len(y1_names) else y_field

            if y1_chart_type == "bar":
                traces.append(
                    {
                        "type": "bar",
                        "name": name,
                        "x": x_values,
                        "y": y_values,
                        "yaxis": "y",
                        "marker": {"color": cls.COLOR_PALETTE[i], "opacity": 0.8},
                    }
                )
            else:
                traces.append(
                    {
                        "type": "scatter",
                        "mode": "lines",
                        "name": name,
                        "x": x_values,
                        "y": y_values,
                        "yaxis": "y",
                        "line": {"color": cls.COLOR_PALETTE[i], "width": 2},
                    }
                )

        # Secondary axis traces
        for i, y_field in enumerate(y2_fields):
            y_values = [d.get(y_field) for d in data]
            name = y2_names[i] if y2_names and i < len(y2_names) else y_field

            if y2_chart_type == "bar":
                traces.append(
                    {
                        "type": "bar",
                        "name": name,
                        "x": x_values,
                        "y": y_values,
                        "yaxis": "y2",
                        "marker": {"color": cls.COLOR_PALETTE[len(y1_fields) + i], "opacity": 0.8},
                    }
                )
            else:
                traces.append(
                    {
                        "type": "scatter",
                        "mode": "lines",
                        "name": name,
                        "x": x_values,
                        "y": y_values,
                        "yaxis": "y2",
                        "line": {
                            "color": cls.COLOR_PALETTE[len(y1_fields) + i],
                            "width": 2,
                            "dash": "dot",
                        },
                    }
                )

        layout = {
            **cls.DEFAULT_LAYOUT,
            "title": {"text": title, "x": 0.5},
            "xaxis": {
                **cls.DEFAULT_LAYOUT["xaxis"],
                "title": x_label,
                "type": "date" if "timestamp" in x_field.lower() else "-",
            },
            "yaxis": {
                **cls.DEFAULT_LAYOUT["yaxis"],
                "title": y1_label,
                "side": "left",
            },
            "yaxis2": {
                "title": y2_label,
                "side": "right",
                "overlaying": "y",
                "showgrid": False,
            },
            "legend": {"x": 0.5, "y": -0.15, "orientation": "h", "xanchor": "center"},
        }

        return {"data": traces, "layout": layout}

    @classmethod
    def scatter_3d_chart(
        cls,
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
        marker_size: int = 5,
        marker_opacity: float = 0.8,
        colorscale: str = "Viridis",
    ) -> Dict[str, Any]:
        """Build a 3D scatter chart specification.

        Args:
            data: List of data records
            x_field: Field name for x-axis
            y_field: Field name for y-axis
            z_field: Field name for z-axis
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            z_label: Z-axis label
            color_field: Optional field for color scale
            color_label: Label for colorbar
            marker_size: Marker size
            marker_opacity: Marker opacity
            colorscale: Plotly colorscale name

        Returns:
            Complete Plotly figure specification
        """
        x_values = [d.get(x_field) for d in data]
        y_values = [d.get(y_field) for d in data]
        z_values = [d.get(z_field) for d in data]

        marker = {
            "size": marker_size,
            "opacity": marker_opacity,
        }

        if color_field:
            color_values = [d.get(color_field) for d in data]
            marker["color"] = color_values
            marker["colorscale"] = colorscale
            marker["colorbar"] = {"title": color_label or color_field.replace("_", " ").title()}
        else:
            marker["color"] = cls.COLOR_PALETTE[0]

        traces = [
            {
                "type": "scatter3d",
                "mode": "markers",
                "name": "Data Points",
                "x": x_values,
                "y": y_values,
                "z": z_values,
                "marker": marker,
            }
        ]

        layout = {
            "title": {"text": title, "x": 0.5},
            "scene": {
                "xaxis": {"title": x_label},
                "yaxis": {"title": y_label},
                "zaxis": {"title": z_label},
            },
            "margin": {"l": 0, "r": 0, "t": 50, "b": 0},
            "paper_bgcolor": "rgba(0,0,0,0)",
        }

        return {"data": traces, "layout": layout}

    @classmethod
    def grouped_bar_chart(
        cls,
        data: List[Dict[str, Any]],
        x_field: str,
        y_fields: List[str],
        title: str,
        x_label: str,
        y_label: str,
        series_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build a grouped bar chart specification.

        Args:
            data: List of data records
            x_field: Field name for categories
            y_fields: List of field names for bar values
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            series_names: Names for each bar series

        Returns:
            Complete Plotly figure specification
        """
        x_values = [d.get(x_field) for d in data]
        traces = []

        for i, y_field in enumerate(y_fields):
            y_values = [d.get(y_field) for d in data]
            name = series_names[i] if series_names and i < len(series_names) else y_field

            traces.append(
                {
                    "type": "bar",
                    "name": name,
                    "x": x_values,
                    "y": y_values,
                    "marker": {"color": cls.COLOR_PALETTE[i % len(cls.COLOR_PALETTE)]},
                }
            )

        layout = {
            **cls.DEFAULT_LAYOUT,
            "title": {"text": title, "x": 0.5},
            "xaxis": {
                **cls.DEFAULT_LAYOUT["xaxis"],
                "title": x_label,
                "type": "category",
            },
            "yaxis": {
                **cls.DEFAULT_LAYOUT["yaxis"],
                "title": y_label,
            },
            "barmode": "group",
            "bargap": 0.15,
            "bargroupgap": 0.1,
        }

        return {"data": traces, "layout": layout}
