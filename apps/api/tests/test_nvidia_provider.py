import pytest

from app.providers.base import LLMGenerationError, LLMMessage
from app.providers.nvidia import NvidiaNimProvider


def test_nvidia_provider_missing_api_key_raises_generation_error() -> None:
    provider = NvidiaNimProvider(api_key="", model="meta/llama-3.1-70b-instruct")

    with pytest.raises(LLMGenerationError, match="NVIDIA NIM API key is not configured"):
        provider.generate([LLMMessage(role="user", content="Hello")])
