from collections.abc import Callable
from dataclasses import dataclass

from app.agents.coding import CodingAgent
from app.agents.data_analyst import DataAnalystAgent
from app.agents.devops_agent import DevOpsAgent
from app.agents.knowledge import KnowledgeAgent
from app.agents.research import ResearchAgent
from app.agents.security_auditor import SecurityAuditorAgent
from app.providers.base import LLMProvider
from app.providers.embeddings.base import EmbeddingProvider
from app.retrieval.repository import RetrievalRepository
from app.tools.registry import ToolRegistry


@dataclass(slots=True)
class AgentBuildContext:
    llm_provider: LLMProvider
    tools: ToolRegistry
    embedding_provider: EmbeddingProvider | None = None
    retrieval_repository: RetrievalRepository | None = None
    user_id: str | None = None
    workspace_id: str | None = None


AgentFactory = Callable[[AgentBuildContext], object]


class AgentRegistry:
    def __init__(self, factories: dict[str, AgentFactory]) -> None:
        self._factories = factories

    def build(self, name: str, context: AgentBuildContext) -> object:
        factory = self._factories.get(name)
        if factory is None:
            supported = ", ".join(sorted(self._factories))
            raise ValueError(f"Unsupported agent {name!r}. Supported agents: {supported}.")
        return factory(context)

    def names(self) -> list[str]:
        return sorted(self._factories)


def build_agent_registry() -> AgentRegistry:
    return AgentRegistry(
        factories={
            ResearchAgent.name: lambda context: ResearchAgent(context.llm_provider, context.tools),
            CodingAgent.name: lambda context: CodingAgent(context.llm_provider, context.tools),
            DataAnalystAgent.name: lambda context: DataAnalystAgent(context.llm_provider, context.tools),
            SecurityAuditorAgent.name: lambda context: SecurityAuditorAgent(context.llm_provider, context.tools),
            DevOpsAgent.name: lambda context: DevOpsAgent(context.llm_provider, context.tools),
            KnowledgeAgent.name: lambda context: KnowledgeAgent(
                llm_provider=context.llm_provider,
                embedding_provider=context.embedding_provider,
                retrieval_repository=context.retrieval_repository,
                user_id=context.user_id,
                workspace_id=context.workspace_id,
            ),
        }
    )
