from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class User:
    id: str
    email: str
    name: str
    emailVerified: bool
    createdAt: datetime
    updatedAt: datetime
    image: str | None = None
    preferred_provider: str | None = None


@dataclass(slots=True)
class Workspace:
    id: str
    name: str
    owner_id: str
    created_at: datetime


@dataclass(slots=True)
class WorkspaceMember:
    id: str
    workspace_id: str
    user_id: str
    role: str
    joined_at: datetime


@dataclass(slots=True)
class WorkspaceInvite:
    id: str
    workspace_id: str
    email: str
    role: str
    token: str
    invited_by: str
    status: str
    expires_at: datetime
    created_at: datetime


@dataclass(slots=True)
class Conversation:
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    workspace_id: str | None = None


@dataclass(slots=True)
class Message:
    id: str
    conversation_id: str
    role: str
    content: str
    tool_name: str | None
    created_at: datetime
    tool_output: str | None = None
    agent_name: str | None = None
    tool_arguments: str | None = None
    thought_process: str | None = None
    user_id: str | None = None
    user_name: str | None = None
    user_email: str | None = None


@dataclass(slots=True)
class ToolCall:
    id: str
    conversation_id: str
    message_id: str
    tool_name: str
    agent_name: str
    arguments: str
    output: str
    created_at: datetime


@dataclass(slots=True)
class UserApiKey:
    id: str
    user_id: str
    provider: str
    encrypted_key: str
    created_at: datetime


@dataclass(slots=True)
class Document:
    id: str
    user_id: str
    title: str
    source_type: str
    created_at: datetime
    workspace_id: str | None = None


@dataclass(slots=True)
class DocumentChunk:
    id: str
    document_id: str
    chunk_index: int
    content: str
    created_at: datetime


@dataclass(slots=True)
class RetrievedChunk:
    id: str
    document_id: str
    content: str
    score: float


@dataclass(slots=True)
class Retrieval:
    id: str
    conversation_id: str
    message_id: str
    agent_name: str
    query: str
    chunk_ids: str
    scores: str
    created_at: datetime
