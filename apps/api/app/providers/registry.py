from app.core.config import settings
from app.providers.base import LLMProvider
from app.providers.fallback import FallbackLLMProvider
from app.providers.gemini import GeminiProvider
from app.providers.groq import GroqProvider
from app.providers.nvidia import NvidiaNimProvider

ProviderFactory = type[GeminiProvider] | type[GroqProvider] | type[NvidiaNimProvider]

PROVIDERS: dict[str, ProviderFactory] = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "nvidia": NvidiaNimProvider,
}

DEFAULT_MODELS: dict[str, str] = {
    "gemini": "gemini-3.5-flash",
    "groq": "llama-3.1-8b-instant",
    "nvidia": "meta/llama-3.1-70b-instruct",
}

GEMINI_FALLBACK_MODELS: list[str] = [
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.6-flash",
]


def build_provider(
    api_key: str | None = None,
    provider_name: str | None = None,
    model: str | None = None,
    disable_fallback: bool = False,
) -> LLMProvider:
    provider_name = (provider_name or settings.llm_provider).lower()
    provider_class = PROVIDERS.get(provider_name)
    if provider_class is None:
        supported = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"Unsupported LLM_PROVIDER={provider_name!r}. Supported providers: {supported}.")

    if model and model.strip():
        selected_model = model.strip()
    elif provider_name != settings.llm_provider:
        selected_model = DEFAULT_MODELS.get(provider_name, settings.llm_model)
    else:
        selected_model = settings.llm_model

    effective_key = api_key if api_key is not None else settings.llm_api_key
    primary_provider = provider_class(api_key=effective_key, model=selected_model)

    if disable_fallback or provider_name != "gemini":
        return primary_provider

    # Build fallback chain for Gemini models
    fallback_providers: list[LLMProvider] = [primary_provider]
    for fb_model in GEMINI_FALLBACK_MODELS:
        if fb_model != selected_model:
            fallback_providers.append(GeminiProvider(api_key=effective_key, model=fb_model))

    return FallbackLLMProvider(fallback_providers)
