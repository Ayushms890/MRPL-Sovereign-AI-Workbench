import json
from app.tools.base import ToolResult


class IndustrialAnomalyCheckTool:
    """Deterministic comparison of extracted process parameters against a
    specification (target + operator) or an operating range (min/max).

    This exists so numeric pass/fail and deviation-% decisions are not left
    to free-form LLM arithmetic. The LLM is expected to extract the
    parameter values from a report/document and pass them in structured
    form; this tool only does the comparison math.
    """

    name = "industrial_anomaly_check"
    description = (
        "Compares extracted industrial/refinery process parameters against their operating range "
        "or specification and returns a deterministic status (NORMAL, LOW, HIGH, CRITICAL) with the "
        "deviation percentage for each. Use this for any refinery/plant shift report, equipment "
        "condition report, or process-parameter analysis instead of estimating deviations yourself."
    )
    parameters = {
        "type": "object",
        "properties": {
            "readings": {
                "type": "array",
                "description": "List of extracted parameter readings to evaluate.",
                "items": {
                    "type": "object",
                    "properties": {
                        "parameter": {"type": "string", "description": "Name of the parameter, e.g. 'Product Sulphur'."},
                        "actual": {"type": "number", "description": "The observed/measured value."},
                        "unit": {"type": "string", "description": "Unit of measurement, e.g. 'ppm', 'bar', 'mm/s'."},
                        "min": {"type": "number", "description": "Minimum of the acceptable operating range, if range-based."},
                        "max": {"type": "number", "description": "Maximum of the acceptable operating range, if range-based."},
                        "target": {"type": "number", "description": "Specification limit value, if spec-based (used with target_operator)."},
                        "target_operator": {
                            "type": "string",
                            "enum": ["<=", ">=", "<", ">"],
                            "description": "How 'actual' must relate to 'target' to be normal, e.g. '<=' for a max-sulphur spec.",
                        },
                    },
                    "required": ["parameter", "actual"],
                },
            }
        },
        "required": ["readings"],
    }

    def execute(self, arguments: dict) -> ToolResult:
        readings = arguments.get("readings", [])
        if not readings:
            return ToolResult(content="Error: no readings provided to evaluate.")

        results = [self._evaluate(reading) for reading in readings]
        summary = {
            "evaluated": len(results),
            "normal": sum(1 for r in results if r["status"] == "NORMAL"),
            "abnormal": sum(1 for r in results if r["status"] != "NORMAL"),
            "results": results,
        }
        return ToolResult(content=f"```json:anomaly_analysis\n{json.dumps(summary, indent=2)}\n```")

    @staticmethod
    def _evaluate(reading: dict) -> dict:
        parameter = reading.get("parameter", "unknown")
        actual = reading.get("actual")
        unit = reading.get("unit", "")
        min_v = reading.get("min")
        max_v = reading.get("max")
        target = reading.get("target")
        operator = reading.get("target_operator")

        status = "NORMAL"
        deviation_percent = 0.0
        basis = None

        if target is not None and operator:
            basis = f"{operator} {target} {unit}".strip()
            ok = {
                "<=": actual <= target,
                ">=": actual >= target,
                "<": actual < target,
                ">": actual > target,
            }.get(operator, True)
            if not ok and target != 0:
                deviation_percent = round(((actual - target) / target) * 100, 1)
                status = "HIGH" if actual > target else "LOW"
                if abs(deviation_percent) >= 50:
                    status = "CRITICAL"
        elif min_v is not None and max_v is not None:
            basis = f"{min_v}\u2013{max_v} {unit}".strip()
            if actual < min_v:
                status = "LOW"
                mid = (min_v + max_v) / 2 or 1
                deviation_percent = round(((actual - mid) / mid) * 100, 1)
            elif actual > max_v:
                status = "HIGH"
                mid = (min_v + max_v) / 2 or 1
                deviation_percent = round(((actual - mid) / mid) * 100, 1)
                if actual > max_v * 1.5:
                    status = "CRITICAL"

        return {
            "parameter": parameter,
            "actual": actual,
            "unit": unit,
            "basis": basis,
            "status": status,
            "deviation_percent": deviation_percent,
        }
