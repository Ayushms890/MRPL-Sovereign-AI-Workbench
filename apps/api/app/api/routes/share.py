import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import get_current_user
from app.api.deps_providers import get_conversation_repository
from app.api.schemas import ShareCreateResponse, ShareSnapshotResponse, ConversationResponse
from app.conversations.repository import ConversationRepository
from app.domain.entities import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["share"])


@router.post("/{conversation_id}/share", response_model=ShareCreateResponse)
def share_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> ShareCreateResponse:
    conversation = repo.get_for_user(conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Sharing is disabled in the MRPL version because it uses no Redis backend.",
    )


@router.get(
    "/share/{share_id}",
    response_model=ShareSnapshotResponse,
)
def get_shared_snapshot(
    share_id: str,
) -> ShareSnapshotResponse:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Sharing is disabled in the MRPL version because it uses no Redis backend.",
    )


@router.post("/share/{share_id}/import", response_model=ConversationResponse)
def import_shared_conversation(
    share_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> ConversationResponse:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Sharing is disabled in the MRPL version because it uses no Redis backend.",
    )


@router.delete("/{conversation_id}/share", status_code=status.HTTP_204_NO_CONTENT)
def revoke_share(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> Response:
    conversation = repo.get_for_user(conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Sharing is disabled in the MRPL version because it uses no Redis backend.",
    )
