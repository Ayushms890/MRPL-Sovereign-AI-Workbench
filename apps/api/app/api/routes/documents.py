from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.dependencies import get_current_user, require_workspace_role
from app.api.deps_providers import get_embedding_provider
from app.api.rate_limit_dependencies import rate_limit_by_user
from app.api.schemas import DocumentCreateRequest, DocumentJobResponse, DocumentJobStatusResponse, DocumentResponse
from app.db import get_db_session
from app.domain.entities import User
from app.infrastructure.models import DocumentModel
from app.jobs.document_ingestion import run_document_ingestion_job
from app.jobs.queue import build_job_queue
from app.providers.embeddings.base import EmbeddingProvider

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit_by_user("document_upload", limit=10, window_seconds=3600))],
)
def create_document(
    payload: DocumentCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    embedding_provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    resolved_ws_id: Annotated[str, Depends(require_workspace_role("owner", "member"))],
    workspace_id: str | None = None,
) -> DocumentJobResponse:
    api_key = getattr(embedding_provider, "api_key", None)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Embeddings require a Gemini key; save one in BYOK settings.",
        )

    result = run_document_ingestion_job({
        "user_id": current_user.id,
        "workspace_id": resolved_ws_id,
        "title": payload.title.strip(),
        "content": payload.content,
    })
    return DocumentJobResponse(job_id=f"sync_{result['document_id']}", status="succeeded")


@router.get("/jobs/{job_id}", response_model=DocumentJobStatusResponse)
def get_document_job(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentJobStatusResponse:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Background job tracking is disabled in the MRPL version. Use the synchronous document ingestion path.",
    )


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
    resolved_ws_id: Annotated[str, Depends(require_workspace_role("owner", "member", "viewer"))],
    workspace_id: str | None = None,
) -> list[DocumentResponse]:
    documents = session.scalars(
        select(DocumentModel).where(DocumentModel.workspace_id == resolved_ws_id).order_by(DocumentModel.created_at.desc())
    ).all()
    return [
        DocumentResponse(
            id=doc.id,
            title=doc.title,
            source_type=doc.source_type,
            chunk_count=len(doc.chunks),
            created_at=doc.created_at,
        )
        for doc in documents
    ]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
    _: Annotated[str, Depends(require_workspace_role("owner", "member"))],
) -> None:
    document = session.scalar(
        select(DocumentModel).where(
            DocumentModel.id == document_id,
        )
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    session.delete(document)
    session.commit()
