import time

import httpx

from app.providers.embeddings.base import EmbeddingProvider
from app.providers.embeddings.errors import EmbeddingError


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_TIMEOUT = 120


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Generate vectors through Ollama's native batch embedding endpoint."""

    def __init__(self, model: str, dimensions: int, base_url: str) -> None:
        self.model = model
        self.dimensions = dimensions
        self.base_url = base_url.rstrip("/")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        endpoint = f"{self.base_url}/api/embed"
        payload = {"model": self.model, "input": texts}
        for attempt in range(2):
            try:
                response = httpx.post(endpoint, json=payload, timeout=DEFAULT_TIMEOUT)
                response.raise_for_status()
                embeddings = response.json().get("embeddings")
                if not isinstance(embeddings, list) or len(embeddings) != len(texts):
                    raise EmbeddingError(
                        f"Ollama returned an invalid embedding batch (model={self.model})."
                    )
                try:
                    vectors = [[float(value) for value in embedding] for embedding in embeddings]
                except (TypeError, ValueError) as exc:
                    raise EmbeddingError(
                        f"Ollama returned malformed embedding values (model={self.model})."
                    ) from exc
                for vector in vectors:
                    if len(vector) != self.dimensions:
                        raise EmbeddingError(
                            f"Ollama returned {len(vector)} embedding dimensions, expected {self.dimensions}. "
                            "Set EMBEDDING_DIMENSIONS to the dimension of the pulled Ollama model."
                        )
                return vectors
            except EmbeddingError:
                raise
            except httpx.ConnectError as exc:
                raise EmbeddingError(
                    f"Could not reach Ollama at {self.base_url}. Is Ollama running and reachable from the backend?"
                ) from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in RETRYABLE_STATUS_CODES and attempt == 0:
                    time.sleep(1)
                    continue
                raise EmbeddingError(
                    f"Ollama embedding request failed with HTTP {exc.response.status_code} "
                    f"{exc.response.reason_phrase} (model={self.model}). "
                    f"Confirm it is installed with: ollama pull {self.model}"
                ) from exc
            except httpx.HTTPError as exc:
                if attempt == 0:
                    time.sleep(1)
                    continue
                raise EmbeddingError(
                    f"Ollama embedding request failed with {exc.__class__.__name__} (model={self.model})."
                ) from exc

        raise EmbeddingError(f"Ollama embedding request failed after retry (model={self.model}).")
