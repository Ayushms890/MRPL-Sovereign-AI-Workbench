from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from app.tools.base import ToolResult

class DbInspectorTool:
    name = "db_inspector"
    description = (
        "Inspects database tables, column definitions, index configurations, or query performance. "
        "Use this tool when optimizing SQL queries, inspecting database schemas, or auditing indexing strategies."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list_tables", "inspect_table", "explain_query"],
                "description": "Inspection action to perform.",
            },
            "table_name": {"type": "string", "description": "Table name to inspect (required for inspect_table)."},
            "query": {"type": "string", "description": "SQL query to profile with EXPLAIN (required for explain_query)."},
        },
        "required": ["action"],
    }

    def __init__(self, session: Session | None = None) -> None:
        self.session = session

    def execute(self, arguments: dict) -> ToolResult:
        result_text = self.run(arguments)
        return ToolResult(content=result_text)

    def run(self, arguments: dict) -> str:
        action = arguments.get("action", "list_tables")
        table_name = arguments.get("table_name", "").strip()
        query = arguments.get("query", "").strip()

        if action == "list_tables":
            if not self.session:
                return "Error: Database session is not available."
            try:
                tables = inspect(self.session.get_bind()).get_table_names()
                lines = ["### Database Tables:"]
                inspector = inspect(self.session.get_bind())
                for table in tables:
                    columns = inspector.get_columns(table)
                    col_specs = []
                    for c in columns:
                        type_str = str(c["type"])
                        col_specs.append(f"{c['name']} {type_str}")
                    lines.append(f"- `{table}`: ({', '.join(col_specs)})")
                return "\n".join(lines)
            except Exception as exc:
                return f"Error listing tables: {exc}"

        elif action == "inspect_table":
            if not table_name:
                return "Error: table_name parameter is required for inspect_table action."
            if not self.session:
                return "Error: Database session is not available."
            try:
                inspector = inspect(self.session.get_bind())
                tables = inspector.get_table_names()
                matched_table = None
                for t in tables:
                    if t.lower() == table_name.lower():
                        matched_table = t
                        break

                if not matched_table:
                    return f"Error: Table '{table_name}' does not exist."

                columns = inspector.get_columns(matched_table)
                indexes = inspector.get_indexes(matched_table)

                lines = [f"### Schema for `{matched_table}`:"]
                for c in columns:
                    nullable_str = "NULL" if c.get("nullable", True) else "NOT NULL"
                    default_str = f" DEFAULT {c['default']}" if c.get("default") is not None else ""
                    lines.append(f"- `{c['name']}`: {c['type']} ({nullable_str}{default_str})")

                if indexes:
                    lines.append("\n**Indexes**:")
                    for idx in indexes:
                        cols = ", ".join(idx["column_names"])
                        unique_str = " (Unique)" if idx.get("unique") else ""
                        lines.append(f"- `{idx['name']}` on ({cols}){unique_str}")
                else:
                    lines.append("\n**Indexes**: None")

                return "\n".join(lines)
            except Exception as exc:
                return f"Error inspecting table '{table_name}': {exc}"

        elif action == "explain_query":
            if not query:
                return "Error: query parameter is required for explain_query action."
            if not self.session:
                return "Error: Database session is not available."

            import re
            cleaned_query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
            cleaned_lines = [line.split('--')[0] for line in cleaned_query.splitlines()]
            cleaned_query = " ".join(cleaned_lines).strip()

            if not cleaned_query.lower().startswith("select"):
                return "Error: Only SELECT queries are permitted for query profiling."

            try:
                explain_sql = f"EXPLAIN {query}"
                res = self.session.execute(text(explain_sql))
                plan_rows = [row[0] for row in res.fetchall()]
                plan_text = "\n".join(plan_rows)
                return (
                    f"### Query Plan (EXPLAIN) for:\n```sql\n{query}\n```\n\n"
                    f"**Execution Plan**:\n```\n{plan_text}\n```"
                )
            except Exception as exc:
                return f"Error explaining query: {exc}"

        return f"Error: Unknown action '{action}'."
