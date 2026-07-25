from unittest.mock import MagicMock
from app.agents.graph import MultiAgentGraph
from app.providers.base import LLMMessage, LLMResponse


class ThoughtAndMultiRouteProvider:
    def __init__(self):
        self.calls = 0

    def generate(self, messages: list[LLMMessage], tools=None) -> LLMResponse:
        self.calls += 1
        if self.calls == 1:
            # Planner node returns thought + compound ROUTE: coding, research
            return LLMResponse(
                content="<thought>The user wants C++ addition code AND recent AI news.</thought> ROUTE: coding, research",
                thought="The user wants C++ addition code AND recent AI news."
            )
        if self.calls == 2:
            # Coding agent response
            return LLMResponse(content="```cpp\n#include <iostream>\nint main() { std::cout << 2+2; }\n```")
        if self.calls == 3:
            # Research agent response
            return LLMResponse(content="Recent AI news includes Gemini 2.5 and Claude 3.7 updates.")
        return LLMResponse(content="Done")


def test_thought_extraction_and_multi_intent_routing():
    mock_tools = MagicMock()
    mock_agents = MagicMock()

    # Mock specialist agents built by registry
    coding_agent = MagicMock()
    coding_agent.run.return_value = MagicMock(answer="```cpp\n#include <iostream>\n```", tool_name=None, agent_name="coding")

    research_agent = MagicMock()
    research_agent.run.return_value = MagicMock(answer="Recent AI news: Models updated.", tool_name="web_search", agent_name="research")

    mock_agents.build.side_effect = lambda name, ctx: coding_agent if name == "coding" else research_agent

    provider = ThoughtAndMultiRouteProvider()

    graph = MultiAgentGraph(
        llm_provider=provider,
        tools=mock_tools,
        agents=mock_agents,
    )

    result = graph.run(user_input="Write cpp addition code and search recent AI news")

    assert result.agent_name == "planner + coding + research"
    assert "Code Solution" in result.answer
    assert "Web Research & News" in result.answer
    assert result.thought_process == "The user wants C++ addition code AND recent AI news."
