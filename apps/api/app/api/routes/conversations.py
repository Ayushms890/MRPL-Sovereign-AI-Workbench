import asyncio
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from app.agents.planner import PlannerAgent
from app.api.dependencies import get_current_user
from app.api.deps_providers import get_conversation_repository, get_planner_agent, get_redis_cache
from app.api.rate_limit_dependencies import rate_limit_by_user
from app.api.schemas import (
    AgentJobResponse,
    AgentJobStatusResponse,
    ConversationCreateRequest,
    ConversationResponse,
    ConversationUpdateRequest,
    MessageCreateRequest,
    MessageResponse,
)
from app.cache.redis_client import RedisCache
from app.conversations.repository import ConversationRepository
from app.conversations.summarization import build_effective_history
from app.domain.entities import Conversation, Message, User
from app.jobs.queue import build_job_queue, JobQueueError


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResponse])
def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> list[ConversationResponse]:
    conversations = repo.list_for_user(current_user.id)
    return [_conversation_response(conversation) for conversation in conversations]


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> ConversationResponse:
    conversation = repo.create(user_id=current_user.id, title=payload.title.strip())
    return _conversation_response(conversation)


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def list_messages(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> list[MessageResponse]:
    _require_conversation(repo, conversation_id, current_user.id)
    return [_message_response(message) for message in repo.list_messages(conversation_id)]


@router.post(
    "/{conversation_id}/messages",
    response_model=AgentJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit_by_user("chat_message", limit=20, window_seconds=60))],
)
def send_message(
    conversation_id: str,
    payload: MessageCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
    cache: Annotated[RedisCache | None, Depends(get_redis_cache)] = None,
) -> AgentJobResponse:
    _require_conversation(repo, conversation_id, current_user.id)

    queue = build_job_queue()
    if queue is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat requires Redis to be configured (UPSTASH_REDIS_REST_URL/TOKEN).",
        )

    # Concurrency Lock Guard: check if an active job is already running for this conversation
    if cache:
        lock_key = f"active_chat_job:{conversation_id}"
        existing_job_id = cache.get(lock_key)
        if existing_job_id:
            try:
                job = queue.get(existing_job_id)
                if job and job.status.value in ["queued", "running"]:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Archimedes is currently answering a query in this conversation. Please wait until it completes.",
                    )
            except JobQueueError as exc:
                logger.error("Error checking existing job status: %s", exc)

    content = payload.content.strip()
    user_message = repo.add_message(conversation_id=conversation_id, role="user", content=content)

    try:
        job = queue.enqueue(
            "chat_agent_run",
            {
                "conversation_id": conversation_id,
                "user_id": current_user.id,
                "user_message_id": user_message.id,
                "content": content,
            },
        )
        if cache:
            # Set the concurrency lock for 5 minutes (300 seconds)
            cache.set(lock_key, job.id, ttl_seconds=300)
    except JobQueueError as exc:
        repo.delete_message(user_message.id)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return AgentJobResponse(job_id=job.id, status=job.status.value, user_message=_message_response(user_message))


# EXPERIMENTAL/UNUSED-BY-DEFAULT: Synchronous SSE chat endpoint.
# Reintroducing this as default can block the FastAPI event loop for concurrent users.
@router.post(
    "/{conversation_id}/messages/stream",
    dependencies=[Depends(rate_limit_by_user("chat_message_stream", limit=30, window_seconds=60))],
)
async def stream_message(
    conversation_id: str,
    payload: MessageCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
    agent: Annotated[PlannerAgent, Depends(get_planner_agent)],
    cache: Annotated[RedisCache | None, Depends(get_redis_cache)] = None,
) -> StreamingResponse:
    _require_conversation(repo, conversation_id, current_user.id)

    content = payload.content.strip()
    user_message = repo.add_message(conversation_id=conversation_id, role="user", content=content)

    async def event_generator():
        all_messages = [
            m for m in repo.list_messages(conversation_id)
            if m.id != user_message.id
        ]
        history = build_effective_history(
            messages=all_messages,
            llm_provider=getattr(agent, "llm_provider", None),
            cache=cache,
            conversation_id=conversation_id,
        )

        yield f"event: thinking\ndata: {json.dumps({'status': 'Planner analyzing prompt...'})}\n\n"
        await asyncio.sleep(0.01)

        try:
            result = agent.run(user_input=content, history=history)

            if result.thought_process:
                yield f"event: thought\ndata: {json.dumps({'thought': result.thought_process})}\n\n"
                await asyncio.sleep(0.01)

            if result.agent_name:
                yield f"event: agent_route\ndata: {json.dumps({'agent_name': result.agent_name})}\n\n"
                await asyncio.sleep(0.01)

            if result.tool_name:
                tool_args = result.tool_arguments if isinstance(getattr(result, "tool_arguments", None), dict) else {}
                yield f"event: tool_start\ndata: {json.dumps({'tool_name': result.tool_name, 'tool_arguments': tool_args})}\n\n"
                await asyncio.sleep(0.01)

            answer = result.answer
            chunk_size = 16
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i:i + chunk_size]
                yield f"event: token\ndata: {json.dumps({'delta': chunk})}\n\n"
                await asyncio.sleep(0.01)

            assistant_message = repo.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=answer,
                tool_name=result.tool_name,
            )
            yield f"event: done\ndata: {json.dumps({'message_id': assistant_message.id, 'role': 'assistant', 'content': answer, 'tool_name': result.tool_name})}\n\n"

        except Exception as exc:
            logger.error("Error during streaming chat execution: %s", exc, exc_info=True)
            error_text = f"Request failed: {exc}"
            repo.add_message(conversation_id=conversation_id, role="assistant", content=error_text)
            yield f"event: error\ndata: {json.dumps({'error': error_text})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{conversation_id}/messages/jobs/{job_id}", response_model=AgentJobStatusResponse)
def get_message_job(
    conversation_id: str,
    job_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> AgentJobStatusResponse:
    queue = build_job_queue()
    if queue is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Job queue unavailable.")
    try:
        job = queue.get(job_id)
    except JobQueueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    if (
        job is None
        or job.payload.get("user_id") != current_user.id
        or job.payload.get("conversation_id") != conversation_id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    assistant_message = None
    if job.result is not None:
        assistant_message = MessageResponse(
            id=job.result["id"],
            role=job.result["role"],
            content=job.result["content"],
            tool_name=job.result.get("tool_name"),
            tool_output=job.result.get("tool_output"),
            agent_name=job.result.get("agent_name"),
            tool_arguments=job.result.get("tool_arguments"),
            thought_process=job.result.get("thought_process"),
            created_at=job.result["created_at"],
        )
    return AgentJobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        assistant_message=assistant_message,
        execution_steps=job.execution_steps,
        error=job.error,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> Response:
    deleted = repo.delete(conversation_id=conversation_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    payload: ConversationUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> ConversationResponse:
    conversation = repo.update_title(conversation_id=conversation_id, user_id=current_user.id, title=payload.title.strip())
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return _conversation_response(conversation)


def _require_conversation(repo: ConversationRepository, conversation_id: str, user_id: str) -> Conversation:
    conversation = repo.get_for_user(conversation_id=conversation_id, user_id=user_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


def _conversation_response(conversation: Conversation) -> ConversationResponse:
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _message_response(message: Message) -> MessageResponse:
    import json
    tool_args = None
    if message.tool_arguments:
        try:
            tool_args = json.loads(message.tool_arguments)
        except Exception:
            tool_args = {"raw": message.tool_arguments}
    return MessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        tool_name=message.tool_name,
        tool_output=message.tool_output,
        agent_name=message.agent_name,
        tool_arguments=tool_args,
        created_at=message.created_at,
    )
