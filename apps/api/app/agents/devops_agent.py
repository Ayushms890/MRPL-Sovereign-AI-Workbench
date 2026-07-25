import logging
from dataclasses import dataclass
from app.providers.base import LLMMessage, LLMProvider
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

DEVOPS_SYSTEM_PROMPT = """You are the DevOps & Infrastructure Agent in Archimedes AI OS.
Your responsibility is to design infrastructure as code, generate production Dockerfiles, Kubernetes manifests (Deployment, Service, Ingress), Terraform configurations, and GitHub Actions CI/CD workflows.

Always provide clean, secure, and production-grade deployment configurations."""

@dataclass(slots=True)
class DevOpsResult:
    answer: str
    tool_name: str | None = None
    tool_arguments: dict | None = None
    tool_output: str | None = None
    agent_name: str = "devops"

class DevOpsAgent:
    name = "devops"

    def __init__(self, llm_provider: LLMProvider, tools: ToolRegistry) -> None:
        self.llm_provider = llm_provider
        self.tools = tools

    def run(self, user_input: str, history: list[LLMMessage] | None = None) -> DevOpsResult:
        messages = [
            LLMMessage(role="system", content=DEVOPS_SYSTEM_PROMPT),
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
                return DevOpsResult(
                    answer=final_response.content,
                    tool_name=response.tool_call.name,
                    tool_arguments=response.tool_call.arguments,
                    tool_output=tool_result.content,
                )

        return DevOpsResult(answer=response.content)
