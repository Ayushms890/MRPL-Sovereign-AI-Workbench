from dataclasses import dataclass

from sqlalchemy.orm import Session
from app.auth.api_key_repository import UserApiKeyRepository
from app.auth.encryption import EncryptionService
from app.core.config import settings


@dataclass(frozen=True)
class ResolvedProviderConfig:
    provider_name: str
    api_key: str
    base_url: str | None = None


def _config_from_stored_value(provider: str, stored_value: str) -> ResolvedProviderConfig:
    if provider == "ollama":
        return ResolvedProviderConfig(
            provider_name=provider,
            api_key="",
            base_url=(stored_value or settings.ollama_base_url).rstrip("/"),
        )
    return ResolvedProviderConfig(provider_name=provider, api_key=stored_value)


def resolve_active_provider_config(
    session: Session,
    user_id: str,
    preferred_provider: str | None,
) -> ResolvedProviderConfig:
    """Resolve the user's active LLM provider, including provider-specific config."""
    user_keys = UserApiKeyRepository(session).list_for_user(user_id)
    preferred = preferred_provider.lower() if preferred_provider else None
    user_key = None
    if preferred:
        user_key = next((key for key in user_keys if key.provider == preferred), None)
    elif len(user_keys) == 1:
        user_key = user_keys[0]

    if user_key is not None:
        stored_value = EncryptionService().decrypt(user_key.encrypted_key)  # raises ValueError if corrupted
        return _config_from_stored_value(user_key.provider, stored_value)

    provider_name = settings.llm_provider.lower()
    if provider_name == "ollama":
        return ResolvedProviderConfig(
            provider_name=provider_name,
            api_key="",
            base_url=settings.ollama_base_url.rstrip("/"),
        )
    return ResolvedProviderConfig(provider_name=provider_name, api_key=settings.llm_api_key)


def resolve_active_provider(session: Session, user_id: str, preferred_provider: str | None) -> tuple[str, str]:
    """Resolve (provider_name, api_key) for a user's active LLM provider.
    Falls back to server-configured settings.llm_provider/llm_api_key if no
    usable saved key exists. Raises ValueError if a saved key is corrupted."""
    config = resolve_active_provider_config(session, user_id, preferred_provider)
    return config.provider_name, config.api_key


def resolve_gemini_api_key(session: Session, user_id: str, preferred_provider: str | None) -> str:
    """Resolve the Gemini API key to use for embeddings for a given user.
    Raises ValueError if no usable Gemini key can be resolved (either a dedicated
    Gemini key, or the user's single/preferred key when it happens to be Gemini,
    or falls through to server-configured settings)."""
    gemini_key = UserApiKeyRepository(session).get_for_user_provider(user_id, "gemini")
    if gemini_key is not None:
        return EncryptionService().decrypt(gemini_key.encrypted_key)  # raises ValueError on corrupt key

    provider_name, api_key = resolve_active_provider(session, user_id, preferred_provider)
    if provider_name != "gemini":
        raise ValueError("Embeddings require a Gemini key; save one in BYOK settings.")
    return api_key
