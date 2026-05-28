"""Pydantic models exposed by the Bot API.

These are intentionally **separate** from the internal app-server models
so we can evolve the public surface without touching SDK-shared shapes
that bots & frontend depend on.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field

# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------


class ErrorBody(BaseModel):
    code: str = Field(description='Stable machine-readable error code.')
    message: str = Field(description='Human-readable explanation.')
    details: dict[str, Any] | None = Field(
        default=None,
        description='Optional structured details (validation errors, hints, …).',
    )


class ErrorResponse(BaseModel):
    """Uniform error envelope returned by every Bot API endpoint."""

    error: ErrorBody


# ---------------------------------------------------------------------------
# Identity / whoami
# ---------------------------------------------------------------------------


class BotIdentity(BaseModel):
    """Who the request authenticated as."""

    user_id: str
    email: EmailStr
    display_name: str
    is_admin: bool
    auth_type: Literal['cookie', 'bearer'] = Field(
        description=(
            '``cookie`` for browser sessions, ``bearer`` for ``X-Api-Key`` / '
            '``Authorization: Bearer dostup_pk_*``.'
        ),
    )
    api_key_id: str | None = Field(
        default=None,
        description='If authenticated via API key, the key id (never the secret).',
    )
    scopes: list[str] = Field(
        default_factory=list,
        description='Scopes granted to this token, if any.',
    )


# ---------------------------------------------------------------------------
# API keys
# ---------------------------------------------------------------------------


class ApiKeyInfo(BaseModel):
    """Public view of an API key (no secret material)."""

    id: str
    name: str
    prefix: str = Field(description='First 8 chars of the secret, safe to display.')
    scopes: list[str] = Field(default_factory=list)
    created_at: datetime
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    is_active: bool


class CreateApiKeyRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=160,
        description='Human-readable label (e.g. "telegram-bot-prod").',
    )
    scopes: list[str] = Field(
        default_factory=list,
        description=(
            'Optional permission scopes. Today the server treats keys as '
            'full-access to the issuing user; scopes are stored for future use.'
        ),
    )
    expires_at: datetime | None = Field(
        default=None,
        description='Optional expiry. If omitted the key does not expire.',
    )


class CreateApiKeyResponse(BaseModel):
    """Returned only at creation time — store the ``token`` immediately."""

    key: ApiKeyInfo
    token: str = Field(
        description=(
            'The plaintext token (`dostup_pk_<id>_<secret>`). Shown **once**; '
            'the server only keeps a hash on disk.'
        ),
    )


class ApiKeyList(BaseModel):
    items: list[ApiKeyInfo]


# ---------------------------------------------------------------------------
# Bot health
# ---------------------------------------------------------------------------


class HealthStatus(BaseModel):
    status: Literal['ok'] = 'ok'
    app_mode: str
    version: str


# ---------------------------------------------------------------------------
# Conversations (simplified shapes the bot API actually returns)
# ---------------------------------------------------------------------------


class ConversationSummary(BaseModel):
    """Trimmed-down conversation info — enough for a bot dashboard."""

    id: str
    title: str | None = None
    sandbox_id: str | None = None
    sandbox_status: str | None = None
    execution_status: str | None = None
    llm_model: str | None = None
    selected_repository: str | None = None
    selected_branch: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ConversationList(BaseModel):
    items: list[ConversationSummary]
    next_page_id: str | None = None


class StartConversationRequest(BaseModel):
    """Bot-friendly shape for starting a new conversation."""

    initial_message: str = Field(
        ..., min_length=1, description='First user message sent to the agent.'
    )
    title: str | None = None
    sandbox_id: str | None = None
    llm_model: str | None = None
    selected_repository: str | None = None
    selected_branch: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class SendMessageRequest(BaseModel):
    """Bot-friendly send-message body. Plain text only — the agent does the rest."""

    content: str = Field(..., min_length=1, description='Plain-text user message.')
    run: bool = Field(
        default=True,
        description='If true, the agent runs immediately after the message lands.',
    )


class SendMessageResult(BaseModel):
    sent: bool
    sandbox_status: str | None = None
    detail: str | None = None
