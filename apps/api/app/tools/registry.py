from sqlalchemy.orm import Session
from app.providers.base import ToolSchema
from app.tools.base import Tool
from app.tools.chart_generator import ChartGeneratorTool
from app.tools.code_execution import CodeExecutionTool
from app.tools.current_time import CurrentTimeTool
from app.tools.db_inspector import DbInspectorTool
from app.tools.github_inspector import GithubInspectorTool
from app.tools.industrial_anomaly_check import IndustrialAnomalyCheckTool
from app.tools.tavily_search import TavilySearchTool
from app.tools.web_reader import WebReaderTool


# Common LLM hallucinations → canonical registered tool names
_TOOL_ALIASES: dict[str, str] = {
    "google_search": "web_search",
    "search_web": "web_search",
    "tavily_search": "web_search",
    "internet_search": "web_search",
    "bing_search": "web_search",
    "run_code": "execute_code",
    "python": "execute_code",
    "python_repl": "execute_code",
}


class ToolRegistry:
    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def get(self, name: str) -> Tool | None:
        # First try exact match, then fall back to alias resolution
        tool = self._tools.get(name)
        if tool is None:
            canonical = _TOOL_ALIASES.get(name)
            if canonical:
                tool = self._tools.get(canonical)
        return tool

    def schemas(self) -> list[ToolSchema]:
        return [
            ToolSchema(name=tool.name, description=tool.description, parameters=tool.parameters)
            for tool in self.all()
        ]


def build_tool_registry(
    session: Session | None = None,
    user_db_session: Session | None = None,
    force_platform_db: bool = False,
) -> ToolRegistry:
    db_session = user_db_session
    if db_session is None and force_platform_db:
        db_session = session

    return ToolRegistry(
        tools=[
            CurrentTimeTool(),
            CodeExecutionTool(),
            TavilySearchTool(),
            WebReaderTool(),
            ChartGeneratorTool(),
            GithubInspectorTool(),
            DbInspectorTool(session=db_session),
            IndustrialAnomalyCheckTool(),
        ]
    )
