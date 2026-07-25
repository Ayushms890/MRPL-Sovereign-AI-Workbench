import logging
from dataclasses import dataclass
from app.providers.base import LLMMessage, LLMProvider
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

SECURITY_AUDITOR_SYSTEM_PROMPT = """You are the Security Auditor Agent in Archimedes AI OS.
Your responsibility is to audit code snippets for security vulnerabilities (OWASP Top 10, SQL injections, hardcoded secrets), recommend security best practices, and output system architecture diagrams.

When requested to provide architecture flowcharts or system designs, ALWAYS output a valid Mermaid.js diagram inside a ```mermaid ``` code block."""

@dataclass(slots=True)
class SecurityAuditorResult:
    answer: str
    tool_name: str | None = None
    tool_arguments: dict | None = None
    tool_output: str | None = None
    agent_name: str = "security_auditor"

class SecurityAuditorAgent:
    name = "security_auditor"

    def __init__(self, llm_provider: LLMProvider, tools: ToolRegistry) -> None:
        self.llm_provider = llm_provider
        self.tools = tools

    def run(self, user_input: str, history: list[LLMMessage] | None = None) -> SecurityAuditorResult:
        messages = [
            LLMMessage(role="system", content=SECURITY_AUDITOR_SYSTEM_PROMPT),
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
                    LLMMessage(role="user", content=f"Tool result: {tool_result.content}"),
                ]
                final_response = self.llm_provider.generate(messages=follow_up_messages)
                return SecurityAuditorResult(
                    answer=final_response.content,
                    tool_name=response.tool_call.name,
                    tool_arguments=response.tool_call.arguments,
                    tool_output=tool_result.content,
                )

        return SecurityAuditorResult(answer=response.content)
