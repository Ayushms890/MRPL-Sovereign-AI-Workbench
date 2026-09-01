import json
import logging
import time

import httpx
from langsmith import traceable

from app.core.config import settings
from app.providers.base import LLMGenerationError, LLMMessage, LLMProvider, LLMResponse, LLMToolCall, ToolSchema

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_TIMEOUT = 120


class OllamaProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or "llama3.1"
        self.base_url = (base_url or getattr(settings, "ollama_base_url", "http://localhost:11434")).rstrip("/")

    @traceable(name="ollama_generate", run_type="llm")
    def generate(self, messages: list[LLMMessage], tools: list[ToolSchema] | None = None) -> LLMResponse:
        payload: dict = {
            "model": self.model,
            "messages": [{"role": message.role, "content": message.content} for message in messages],
            "stream": False,
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                for tool in tools
            ]
            payload["tool_choice"] = "auto"

        endpoint = f"{self.base_url}/v1/chat/completions"
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                response = httpx.post(
                    endpoint,
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                    json=payload,
                    timeout=DEFAULT_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()
                logger.debug("Ollama raw response: %s", data)

                choices = data.get("choices") or []
                if not choices:
                    raise LLMGenerationError(f"Ollama returned no choices in response (model={self.model}).")

                message = choices[0].get("message") or {}
                tool_calls = message.get("tool_calls") or []
                if tool_calls:
                    function = tool_calls[0].get("function", {})
                    fn_args_raw = function.get("arguments", "{}")
                    try:
                        parsed_args = json.loads(fn_args_raw) if isinstance(fn_args_raw, str) else fn_args_raw
                    except Exception:
                        parsed_args = {}
                    return LLMResponse(
                        content=message.get("content") or "",
                        tool_call=LLMToolCall(
                            name=function.get("name", ""),
                            arguments=parsed_args if isinstance(parsed_args, dict) else {},
                        ),
                    )

                return LLMResponse(content=(message.get("content") or "").strip())

            except httpx.ConnectError as exc:
                raise LLMGenerationError(
                    f"Could not reach Ollama at {self.base_url}. Is Ollama running, and is this base URL "
                    "reachable from wherever the backend is deployed? 'localhost' only works when Ollama "
                    "and the backend run on the same machine."
                ) from exc
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                reason = exc.response.reason_phrase
                error_body = exc.response.text
                logger.warning("Ollama HTTP %d %s: %s (attempt %d/%d)", status_code, reason, error_body, attempt + 1, max_attempts)
                if status_code in RETRYABLE_STATUS_CODES and attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise LLMGenerationError(
                    f"Ollama returned HTTP {status_code} {reason} (model={self.model}): {error_body[:300]}. "
                    f"Confirm this model is pulled locally by running: ollama pull {self.model}"
                ) from exc
            except httpx.ReadTimeout as exc:
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise LLMGenerationError(
                    f"Ollama request timed out after {DEFAULT_TIMEOUT}s (model={self.model}). "
                    "Confirm Ollama is running and the selected model is available."
                ) from exc
            except httpx.HTTPError as exc:
                if attempt < max_attempts - 1:
                    time.sleep(1)
                    continue
                raise LLMGenerationError(
                    f"Ollama request failed with {exc.__class__.__name__} (model={self.model})."
                ) from exc

        raise LLMGenerationError(f"Ollama request failed after {max_attempts} attempts (model={self.model}).")
