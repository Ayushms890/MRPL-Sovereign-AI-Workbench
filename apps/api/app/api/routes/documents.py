from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.dependencies import get_current_user, require_workspace_role
from app.api.deps_providers import get_embedding_provider
from app.api.rate_limit_dependencies import rate_limit_by_user
from app.api.schemas import DocumentCreateRequest, DocumentJobResponse, DocumentJobStatusResponse, DocumentResponse
from app.core.config import settings
from app.db import get_db_session
from app.domain.entities import User
from app.infrastructure.models import DocumentModel
from app.providers.embeddings.base import EmbeddingProvider
from app.jobs.queue import build_job_queue, JobQueueError

router = APIRouter(prefix="/documents", tags=["documents"])


def _send_inngest_event(name: str, data: dict) -> bool:
    if settings.environment == "test":
        return False
    try:
        import inngest
        from app.inngest.client import inngest_client

        inngest_client.send_sync(inngest.Event(name=name, data=data))
        return True
    except Exception:
        return False


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
    doc_payload = {
        "user_id": current_user.id,
        "workspace_id": resolved_ws_id,
        "title": payload.title.strip(),
        "content": payload.content,
        "chunk_size": payload.chunk_size,
        "overlap": payload.overlap,
    }

    queue = build_job_queue()
    if queue is not None:
        try:
            from uuid import uuid4

            job_id = str(uuid4())
            doc_payload = {**doc_payload, "job_id": job_id}
            job = queue.create_job("document_ingestion", doc_payload, job_id=job_id)
            dispatched_to_inngest = _send_inngest_event("ai-os/document.uploaded", doc_payload)
            if not dispatched_to_inngest:
                queue.enqueue_existing(job.id)
            return DocumentJobResponse(job_id=job.id, status=job.status.value)
        except Exception:
            pass

    from uuid import uuid4
    from app.jobs.document_ingestion import run_document_ingestion_job
    fallback_job_id = f"sync_doc_{uuid4().hex[:12]}"
    try:
        run_document_ingestion_job(doc_payload)
        return DocumentJobResponse(job_id=fallback_job_id, status="succeeded")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Document ingestion failed: {exc}") from exc


@router.get("/jobs/{job_id}", response_model=DocumentJobStatusResponse)
def get_document_job(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentJobStatusResponse:
    queue = build_job_queue()
    if queue is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Job queue unavailable.")
    try:
        job = queue.get(job_id)
    except JobQueueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    if job is None or job.payload.get("user_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return DocumentJobStatusResponse(
        job_id=job.id, status=job.status.value, result=job.result, error=job.error
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
