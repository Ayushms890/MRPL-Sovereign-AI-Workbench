import httpx
import pytest

from app.providers.base import LLMGenerationError, LLMMessage, ToolSchema
from app.providers.ollama import OllamaProvider


class FakeResponse:
    status_code = 200
    reason_phrase = "OK"
    text = ""

    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_ollama_provider_parses_successful_response(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(url: str, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return FakeResponse({"choices": [{"message": {"content": " Local response. "}}]})

    monkeypatch.setattr("app.providers.ollama.httpx.post", fake_post)

    provider = OllamaProvider(api_key="", model="llama3.1", base_url="http://localhost:11434/")
    response = provider.generate([LLMMessage(role="user", content="Hello")])

    assert captured["url"] == "http://localhost:11434/v1/chat/completions"
    assert captured["json"]["model"] == "llama3.1"
    assert captured["json"]["stream"] is False
    assert response.content == "Local response."


def test_ollama_provider_connect_error_is_actionable(monkeypatch) -> None:
    def fake_post(url: str, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("app.providers.ollama.httpx.post", fake_post)

    provider = OllamaProvider(api_key="", model="llama3.1", base_url="http://localhost:11434")

    with pytest.raises(LLMGenerationError) as exc_info:
        provider.generate([LLMMessage(role="user", content="Hello")])

    message = str(exc_info.value)
    assert "Could not reach Ollama at http://localhost:11434" in message
    assert "localhost" in message
    assert "backend" in message


def test_ollama_provider_parses_tool_call(monkeypatch) -> None:
    def fake_post(url: str, **kwargs):
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "web_search",
                                        "arguments": "{\"query\":\"Ollama tools\"}",
                                    }
                                }
                            ],
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("app.providers.ollama.httpx.post", fake_post)

    provider = OllamaProvider(api_key="", model="llama3.1", base_url="http://localhost:11434")
    response = provider.generate(
        [LLMMessage(role="user", content="Search")],
        tools=[
            ToolSchema(
                name="web_search",
                description="Search the web",
                parameters={"type": "object", "properties": {"query": {"type": "string"}}},
            )
        ],
    )

    assert response.tool_call is not None
    assert response.tool_call.name == "web_search"
    assert response.tool_call.arguments == {"query": "Ollama tools"}
