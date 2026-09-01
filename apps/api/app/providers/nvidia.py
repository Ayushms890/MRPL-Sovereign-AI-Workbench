import json
import logging
import time
import httpx
from langsmith import traceable

from app.core.config import settings
from app.providers.base import LLMGenerationError, LLMMessage, LLMProvider, LLMResponse, LLMToolCall, ToolSchema

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_TIMEOUT = 180  # seconds — large models like minimax-m3 can be slow to cold-start


class NvidiaNimProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or "meta/llama-3.1-70b-instruct"
        self.base_url = (base_url or getattr(settings, "nvidia_base_url", "https://integrate.api.nvidia.com/v1")).rstrip("/")

    @traceable(name="nvidia_generate", run_type="llm")
    def generate(self, messages: list[LLMMessage], tools: list[ToolSchema] | None = None) -> LLMResponse:
        if not self.api_key:
            raise LLMGenerationError(
                "NVIDIA NIM API key is not configured. Set your NVIDIA API key (nvapi-...) "
                "in Settings or apps/api/.env."
            )

        payload: dict = {
            "model": self.model,
            "messages": [{"role": message.role, "content": message.content} for message in messages],
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": settings.llm_max_output_tokens,
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

        endpoint = f"{self.base_url}/chat/completions"
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                response = httpx.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json=payload,
                    timeout=DEFAULT_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()
                logger.debug("NVIDIA NIM raw response: %s", data)

                choices = data.get("choices") or []
                if not choices:
                    raise LLMGenerationError(f"NVIDIA NIM returned no choices in response (model={self.model}).")

                message = choices[0].get("message") or {}
                tool_calls = message.get("tool_calls") or []
                if tool_calls:
                    function = tool_calls[0].get("function", {})
                    fn_name = function.get("name", "")
                    fn_args_raw = function.get("arguments", "{}")
                    try:
                        parsed_args = json.loads(fn_args_raw) if isinstance(fn_args_raw, str) else fn_args_raw
                    except Exception:
                        parsed_args = {}
                    return LLMResponse(
                        content=message.get("content") or "",
                        tool_call=LLMToolCall(
                            name=fn_name,
                            arguments=parsed_args if isinstance(parsed_args, dict) else {},
                        ),
                    )

                return LLMResponse(content=(message.get("content") or "").strip())

            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                reason = exc.response.reason_phrase
                error_body = exc.response.text
                logger.warning("NVIDIA NIM HTTP %d %s: %s (attempt %d/%d)", status_code, reason, error_body, attempt + 1, max_attempts)
                if status_code in RETRYABLE_STATUS_CODES and attempt < max_attempts - 1:
                    continue
                raise LLMGenerationError(
                    f"NVIDIA NIM request failed with HTTP {status_code} {reason} (model={self.model}): {error_body}"
                ) from exc
            except httpx.ReadTimeout as exc:
                wait = 2 ** attempt
                logger.warning("NVIDIA NIM ReadTimeout on attempt %d/%d for model=%s, retrying in %ds", attempt + 1, max_attempts, self.model, wait)
                if attempt < max_attempts - 1:
                    time.sleep(wait)
                    continue
                raise LLMGenerationError(
                    f"NVIDIA NIM request timed out after {DEFAULT_TIMEOUT}s (model={self.model}). "
                    "The model may be cold-starting — please try again in a few seconds."
                ) from exc
            except httpx.HTTPError as exc:
                if attempt < max_attempts - 1:
                    time.sleep(1)
                    continue
                raise LLMGenerationError(
                    f"NVIDIA NIM request failed with {exc.__class__.__name__} (model={self.model})."
                ) from exc

        raise LLMGenerationError(f"NVIDIA NIM request failed after {max_attempts} attempts (model={self.model}).")
