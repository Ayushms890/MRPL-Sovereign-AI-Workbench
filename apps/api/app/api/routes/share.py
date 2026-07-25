import logging
import json
from uuid import uuid4
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.api.deps_providers import get_conversation_repository, get_redis_cache
from app.api.schemas import ShareCreateResponse, ShareSnapshotResponse, ConversationResponse
from app.conversations.repository import ConversationRepository
from app.cache.redis_client import RedisCache
from app.domain.entities import User
from app.tools.repository import ToolCallRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["share"])


@router.post("/{conversation_id}/share", response_model=ShareCreateResponse)
def share_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
    cache: Annotated[RedisCache | None, Depends(get_redis_cache)] = None,
) -> ShareCreateResponse:
    if cache is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sharing requires Redis to be configured."
        )

    # 1. Fetch conversation and check ownership
    conversation = repo.get_for_user(conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # 2. Fetch all messages
    messages = repo.list_messages(conversation_id)

    # 3. Serialize snapshot payload
    serialized_messages = []
    for msg in messages:
        serialized_messages.append({
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "tool_name": msg.tool_name,
            "created_at": msg.created_at.isoformat() if hasattr(msg.created_at, "isoformat") else str(msg.created_at),
            "tool_output": msg.tool_output,
            "agent_name": msg.agent_name,
            "tool_arguments": msg.tool_arguments,
            "thought_process": msg.thought_process,
        })

    payload = {
        "title": conversation.title,
        "messages": serialized_messages
    }

    # 4. Save to Redis with a unique share_id
    share_id = str(uuid4())
    cache_key = f"shared_chat:{share_id}"
    try:
        # Save indefinitely
        cache.client.set(cache_key, json.dumps(payload))
    except Exception as exc:
        logger.exception("Failed to write share snapshot to Redis")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to persist share snapshot.") from exc

    return ShareCreateResponse(share_id=share_id, title=conversation.title)


@router.get("/share/{share_id}", response_model=ShareSnapshotResponse)
def get_shared_snapshot(
    share_id: str,
    cache: Annotated[RedisCache | None, Depends(get_redis_cache)] = None,
) -> ShareSnapshotResponse:
    if cache is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sharing queries require Redis to be configured."
        )

    cache_key = f"shared_chat:{share_id}"
    try:
        raw_data = cache.client.get(cache_key)
    except Exception as exc:
        logger.exception("Failed to read share snapshot from Redis")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch share snapshot.") from exc

    if not raw_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared chat not found or expired")

    try:
        data = json.loads(raw_data)
    except Exception as exc:
        logger.error("Failed to parse shared chat snapshot: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Malformed share snapshot.") from exc

    return ShareSnapshotResponse(title=data["title"], messages=data["messages"])


@router.post("/share/{share_id}/import", response_model=ConversationResponse)
def import_shared_conversation(
    share_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
    cache: Annotated[RedisCache | None, Depends(get_redis_cache)] = None,
) -> ConversationResponse:
    if cache is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sharing actions require Redis to be configured."
        )

    # 1. Fetch snapshot from Redis
    cache_key = f"shared_chat:{share_id}"
    try:
        raw_data = cache.client.get(cache_key)
    except Exception as exc:
        logger.exception("Failed to read share snapshot from Redis during import")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch share snapshot.") from exc

    if not raw_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared chat not found or expired")

    try:
        data = json.loads(raw_data)
    except Exception as exc:
        logger.error("Failed to parse shared chat snapshot for import: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Malformed share snapshot.") from exc

    # 2. Create a new conversation for current user
    new_conv = repo.create(user_id=current_user.id, title=data["title"])

    # 3. Copy all messages and their tool calls
    tool_repo = ToolCallRepository(repo.session)
    for msg in data["messages"]:
        new_msg = repo.add_message(
            conversation_id=new_conv.id,
            role=msg["role"],
            content=msg["content"],
            tool_name=msg.get("tool_name"),
        )
        if msg.get("tool_name") and (msg.get("tool_arguments") is not None or msg.get("tool_output") is not None):
            args_str = json.dumps(msg["tool_arguments"]) if isinstance(msg["tool_arguments"], dict) else str(msg["tool_arguments"] or "")
            tool_repo.create(
                conversation_id=new_conv.id,
                message_id=new_msg.id,
                tool_name=msg["tool_name"],
                agent_name=msg.get("agent_name") or "planner",
                arguments=args_str,
                output=msg.get("tool_output") or "",
            )

    return ConversationResponse(
        id=new_conv.id,
        title=new_conv.title,
        created_at=new_conv.created_at,
        updated_at=new_conv.updated_at,
    )
