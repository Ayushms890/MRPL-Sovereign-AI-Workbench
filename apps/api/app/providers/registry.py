from app.core.config import settings
from app.providers.base import LLMProvider
from app.providers.fallback import FallbackLLMProvider
from app.providers.gemini import GeminiProvider
from app.providers.groq import GroqProvider
from app.providers.nvidia import NvidiaNimProvider
from app.providers.ollama import OllamaProvider

ProviderFactory = type[GeminiProvider] | type[GroqProvider] | type[NvidiaNimProvider] | type[OllamaProvider]

PROVIDERS: dict[str, ProviderFactory] = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "nvidia": NvidiaNimProvider,
    "ollama": OllamaProvider,
}

DEFAULT_MODELS: dict[str, str] = {
    "gemini": "gemini-3.5-flash",
    "groq": "llama-3.1-8b-instant",
    "nvidia": "meta/llama-3.1-70b-instruct",
    "ollama": "llama3.1",
}

GEMINI_FALLBACK_MODELS: list[str] = [
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.6-flash",
]

NVIDIA_FALLBACK_MODELS: list[str] = [
    "meta/llama-3.1-8b-instruct",
]

FALLBACK_MODELS_BY_PROVIDER: dict[str, list[str]] = {
    "gemini": GEMINI_FALLBACK_MODELS,
    "nvidia": NVIDIA_FALLBACK_MODELS,
}


def build_provider(
    api_key: str | None = None,
    provider_name: str | None = None,
    model: str | None = None,
    disable_fallback: bool = False,
    base_url: str | None = None,
) -> LLMProvider:
    provider_name = (provider_name or settings.llm_provider).lower()
    settings_provider_name = settings.llm_provider.lower()
    provider_class = PROVIDERS.get(provider_name)
    if provider_class is None:
        supported = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"Unsupported LLM_PROVIDER={provider_name!r}. Supported providers: {supported}.")

    if model and model.strip():
        selected_model = model.strip()
    elif provider_name != settings_provider_name:
        selected_model = DEFAULT_MODELS.get(provider_name, settings.llm_model)
    else:
        selected_model = settings.llm_model

    effective_key = api_key if api_key is not None else settings.llm_api_key
    provider_kwargs = {"api_key": effective_key, "model": selected_model}
    if provider_name in {"nvidia", "ollama"}:
        provider_kwargs["base_url"] = base_url or (
            settings.ollama_base_url if provider_name == "ollama" else settings.nvidia_base_url
        )
    primary_provider = provider_class(**provider_kwargs)

    fallback_models = FALLBACK_MODELS_BY_PROVIDER.get(provider_name, [])
    if disable_fallback or not fallback_models:
        return primary_provider

    fallback_providers: list[LLMProvider] = [primary_provider]
    for fb_model in fallback_models:
        if fb_model != selected_model:
            fallback_kwargs = {"api_key": effective_key, "model": fb_model}
            if provider_name == "nvidia":
                fallback_kwargs["base_url"] = base_url or settings.nvidia_base_url
            fallback_providers.append(provider_class(**fallback_kwargs))

    return FallbackLLMProvider(fallback_providers)
