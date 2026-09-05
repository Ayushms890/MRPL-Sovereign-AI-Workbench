from app.auth.provider_resolution import resolve_embedding_provider_config
from app.core.config import settings
from app.db import SessionLocal, get_engine
from app.infrastructure.models import UserModel
from app.providers.embeddings.gemini import GeminiEmbeddingProvider
from app.providers.embeddings.ollama import OllamaEmbeddingProvider
from app.retrieval.chunking import chunk_text
from app.retrieval.repository import DocumentRepository


def run_document_ingestion_job(payload: dict) -> dict:
    """payload: {"user_id": str, "title": str, "content": str}"""
    get_engine()
    session = SessionLocal()
    try:
        user_id = payload["user_id"]
        user_model = session.get(UserModel, user_id)
        if not user_model:
            raise ValueError("User not found")
        provider_config = resolve_embedding_provider_config(session, user_id, user_model.preferred_provider)

        chunk_size = payload.get("chunk_size") or settings.default_chunk_size
        overlap = payload.get("overlap") if payload.get("overlap") is not None else settings.default_chunk_overlap
        chunks = chunk_text(payload["content"], chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            raise ValueError("Document content is empty after chunking")

        if provider_config.provider_name == "ollama":
            embedding_provider = OllamaEmbeddingProvider(
                model=settings.ollama_embedding_model,
                dimensions=settings.embedding_dimensions,
                base_url=provider_config.base_url or settings.ollama_base_url,
            )
        else:
            embedding_provider = GeminiEmbeddingProvider(
                api_key=provider_config.api_key,
                model=settings.embedding_model,
                dimensions=settings.embedding_dimensions,
            )
        embeddings = embedding_provider.embed(chunks)

        document = DocumentRepository(session).create_with_chunks(
            user_id=user_id,
            workspace_id=payload.get("workspace_id"),
            title=payload["title"],
            source_type="pasted_text",
            chunks=chunks,
            embeddings=embeddings,
        )
        return {
            "document_id": document.id,
            "title": document.title,
            "chunk_count": len(chunks),
        }
    finally:
        session.close()
