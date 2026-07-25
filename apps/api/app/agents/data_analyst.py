import logging
from dataclasses import dataclass
from app.providers.base import LLMMessage, LLMProvider
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

DATA_ANALYST_SYSTEM_PROMPT = """You are the Data Analyst Agent in Archimedes AI OS.
Your responsibility is to analyze data queries, process CSV/JSON datasets, write clean SQL queries, and generate data visualizations.
If the user asks to visualize data or plot statistics, invoke the `chart_generator` tool.
If the user asks about database schemas or index optimizations, invoke the `db_inspector` tool.

CRITICAL INSTRUCTION FOR CHARTS:
When the `chart_generator` tool is invoked, YOU MUST ALWAYS INCLUDE THE ENTIRE ````json:chart ... ```` CODE BLOCK FROM THE TOOL RESULT AT THE BEGINNING OF YOUR RESPONSE SO THE FRONTEND CAN RENDER THE INTERACTIVE GRAPH."""

@dataclass(slots=True)
class DataAnalystResult:
    answer: str
    tool_name: str | None = None
    tool_arguments: dict | None = None
    tool_output: str | None = None
    agent_name: str = "data_analyst"

class DataAnalystAgent:
    name = "data_analyst"

    def __init__(self, llm_provider: LLMProvider, tools: ToolRegistry) -> None:
        self.llm_provider = llm_provider
        self.tools = tools

    def run(self, user_input: str, history: list[LLMMessage] | None = None) -> DataAnalystResult:
        messages = [
            LLMMessage(role="system", content=DATA_ANALYST_SYSTEM_PROMPT),
            *(history or []),
            LLMMessage(role="user", content=user_input),
        ]

        schemas = self.tools.schemas()
        response = self.llm_provider.generate(messages=messages, tools=schemas)

        if response.tool_call:
            tool = self.tools.get(response.tool_call.name)
            if tool:
                tool_result = tool.execute(response.tool_call.arguments)
                follow_up_messages = [
                    *messages,
                    LLMMessage(role="assistant", content=f"Tool call: {response.tool_call.name}"),
                    LLMMessage(
                        role="user",
                        content=(
                            f"Tool result: {tool_result.content}\n\n"
                            "IMPORTANT: You MUST include any ```json:chart ... ``` code block from the tool result in your final answer so the interactive chart is rendered."
                        ),
                    ),
                ]
                final_response = self.llm_provider.generate(messages=follow_up_messages)
                
                final_answer = final_response.content
                # Fail-safe: If the LLM omitted the ```json:chart block, prepend it automatically
                if "```json:chart" in tool_result.content and "```json:chart" not in final_answer:
                    final_answer = f"{tool_result.content}\n\n{final_answer}"

                return DataAnalystResult(
                    answer=final_answer,
                    tool_name=response.tool_call.name,
                    tool_arguments=response.tool_call.arguments,
                    tool_output=tool_result.content,
                )

        return DataAnalystResult(answer=response.content)
