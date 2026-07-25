import json
from app.tools.base import ToolResult

class ChartGeneratorTool:
    name = "chart_generator"
    description = (
        "Generates a data visualization chart specification (bar chart, line graph, pie chart, or area chart). "
        "Use this tool when the user asks to visualize data, plot metrics, or show statistical trends."
    )
    parameters = {
        "type": "object",
        "properties": {
            "chart_type": {
                "type": "string",
                "enum": ["bar", "line", "pie", "area"],
                "description": "Type of chart to generate (bar, line, pie, or area).",
            },
            "title": {"type": "string", "description": "Title of the chart."},
            "data": {
                "type": "array",
                "description": "List of data points where each item is a dictionary with labels and numeric values.",
                "items": {"type": "object"},
            },
            "x_key": {"type": "string", "description": "The dictionary key to use for the X-axis label."},
            "y_keys": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of dictionary keys to plot on the Y-axis.",
            },
        },
        "required": ["chart_type", "title", "data", "x_key", "y_keys"],
    }

    def execute(self, arguments: dict) -> ToolResult:
        result_text = self.run(arguments)
        return ToolResult(content=result_text)

    def run(self, arguments: dict) -> str:
        chart_type = arguments.get("chart_type", "bar")
        title = arguments.get("title", "Data Visualization")
        data = arguments.get("data", [])
        x_key = arguments.get("x_key", "")
        y_keys = arguments.get("y_keys", [])

        if not data:
            return "Error: Chart data cannot be empty."

        chart_spec = {
            "chart_type": chart_type,
            "title": title,
            "data": data,
            "x_key": x_key,
            "y_keys": y_keys,
        }

        spec_json = json.dumps(chart_spec, indent=2)
        return f"```json:chart\n{spec_json}\n```\n\nGenerated {chart_type.upper()} chart: **{title}** with {len(data)} data points."
