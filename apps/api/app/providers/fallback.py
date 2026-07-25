import logging
from app.providers.base import LLMGenerationError, LLMMessage, LLMProvider, LLMResponse, ToolSchema

logger = logging.getLogger(__name__)


class FallbackLLMProvider:
    def __init__(self, providers: list[LLMProvider]) -> None:
        if not providers:
            raise ValueError("FallbackLLMProvider requires at least one LLM provider.")
        self.providers = providers

    @property
    def api_key(self) -> str | None:
        return getattr(self.providers[0], "api_key", None)

    @property
    def model(self) -> str | None:
        return getattr(self.providers[0], "model", None)

    def generate(self, messages: list[LLMMessage], tools: list[ToolSchema] | None = None) -> LLMResponse:
        last_exception: Exception | None = None
        for idx, provider in enumerate(self.providers):
            provider_label = getattr(provider, "model", type(provider).__name__)
            try:
                response = provider.generate(messages, tools=tools)
                return response
            except Exception as exc:
                last_exception = exc
                logger.warning(
                    f"LLM Provider [{provider_label}] failed (attempt {idx + 1}/{len(self.providers)}): {exc}. "
                    "Failing over to next provider in fallback chain..."
                )

        raise LLMGenerationError(
            f"All LLM providers in fallback chain failed ({len(self.providers)} attempted). Last error: {last_exception}"
        )
