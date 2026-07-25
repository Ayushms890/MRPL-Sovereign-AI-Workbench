from unittest.mock import MagicMock
import pytest

from app.providers.base import LLMGenerationError, LLMMessage, LLMResponse
from app.providers.fallback import FallbackLLMProvider
from app.providers.registry import build_provider


def test_fallback_provider_primary_success():
    primary = MagicMock()
    primary.generate.return_value = LLMResponse(content="Primary Success")
    secondary = MagicMock()

    fallback = FallbackLLMProvider([primary, secondary])
    response = fallback.generate([LLMMessage(role="user", content="Hello")])

    assert response.content == "Primary Success"
    primary.generate.assert_called_once()
    secondary.generate.assert_not_called()


def test_fallback_provider_primary_fails_secondary_succeeds():
    primary = MagicMock()
    primary.generate.side_effect = LLMGenerationError("429 Rate Limit Exceeded")
    primary.model = "gemini-3.5-flash"

    secondary = MagicMock()
    secondary.generate.return_value = LLMResponse(content="Fallback Success")
    secondary.model = "gemini-3.5-flash-lite"

    fallback = FallbackLLMProvider([primary, secondary])
    response = fallback.generate([LLMMessage(role="user", content="Hello")])

    assert response.content == "Fallback Success"
    assert primary.generate.call_count == 1
    assert secondary.generate.call_count == 1


def test_fallback_provider_all_fail_raises_error():
    p1 = MagicMock()
    p1.generate.side_effect = LLMGenerationError("429 Rate Limit")
    p2 = MagicMock()
    p2.generate.side_effect = LLMGenerationError("503 Service Unavailable")

    fallback = FallbackLLMProvider([p1, p2])
    with pytest.raises(LLMGenerationError) as exc_info:
        fallback.generate([LLMMessage(role="user", content="Hello")])

    assert "All LLM providers in fallback chain failed" in str(exc_info.value)


def test_build_provider_returns_fallback_wrapper():
    provider = build_provider(api_key="test-key", provider_name="gemini", model="gemini-3.5-flash")
    assert isinstance(provider, FallbackLLMProvider)
    assert len(provider.providers) >= 2
