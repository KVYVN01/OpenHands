"""Public Bot API for DOSTUP_CRS.

Endpoints under ``/api/v1/bot`` are the **stable, documented** surface
for bots and external automation. They accept either:

* a browser session cookie (``dostup_session``), or
* a long-lived API key passed via ``X-Api-Key`` or
  ``Authorization: Bearer dostup_pk_<id>_<secret>``.

The router intentionally keeps payloads compact so a third-party bot
does not need to understand the agent SDK's full event protocol to do
basic things like list conversations or fetch identity. For sending
messages and reading events the bot should use the existing tested
endpoints (``/api/v1/app-conversations/...`` and
``/api/v1/conversation/{id}/events``), which also accept API-key auth.
"""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from openhands.app_server.app_conversation.app_conversation_info_service import (
    AppConversationInfoService,
)
from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversation,
    AppConversationInfo,
    AppConversationSortOrder,
)
from openhands.app_server.app_conversation.app_conversation_service import (
    AppConversationService,
)
from openhands.app_server.bot_api.dependencies import (
    build_identity,
    require_admin,
    require_user,
)
from openhands.app_server.bot_api.schemas import (
    BotIdentity,
    ConversationList,
    ConversationSummary,
    HealthStatus,
)
from openhands.app_server.bot_api.scopes import require_scope
from openhands.app_server.config import (
    depends_app_conversation_info_service,
    depends_app_conversation_service,
    get_global_config,
)
from openhands.app_server.user_auth.dostup.dostup_user_auth import DostupUserAuth
from openhands.app_server.version import get_version

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/bot', tags=['Bot API'])

_conversation_service_dep = depends_app_conversation_service()
_conversation_info_service_dep = depends_app_conversation_info_service()


def _conversation_to_summary(
    convo: AppConversation | AppConversationInfo,
) -> ConversationSummary:
    """Project the verbose internal model down to the bot-facing summary."""
    return ConversationSummary(
        id=str(convo.id),
        title=convo.title,
        sandbox_id=convo.sandbox_id,
        sandbox_status=getattr(getattr(convo, 'sandbox_status', None), 'value', None),
        execution_status=getattr(
            getattr(convo, 'execution_status', None), 'value', None
        ),
        llm_model=convo.llm_model,
        selected_repository=convo.selected_repository,
        selected_branch=convo.selected_branch,
        tags=dict(convo.tags or {}),
        created_at=convo.created_at,
        updated_at=convo.updated_at,
    )


# ---------------------------------------------------------------------------
# Health & identity
# ---------------------------------------------------------------------------


@router.get(
    '/health',
    summary='Lightweight readiness probe',
    response_model=HealthStatus,
)
async def health() -> HealthStatus:
    """Unauthenticated health check. Safe to expose to monitoring."""
    mode_value = getattr(get_global_config().app_mode, 'value', 'oss')
    return HealthStatus(app_mode=str(mode_value), version=get_version())


@router.get(
    '/whoami',
    summary='Identity of the authenticated principal',
    response_model=BotIdentity,
)
async def whoami(
    request: Request,
    auth: DostupUserAuth = Depends(require_user),
) -> BotIdentity:
    """Return who the server thinks is making the call, plus the auth method."""
    return await build_identity(request, auth)


# ---------------------------------------------------------------------------
# Conversations (read-only, simplified shapes)
# ---------------------------------------------------------------------------


@router.get(
    '/conversations',
    summary="List the current user's conversations",
    response_model=ConversationList,
    dependencies=[Depends(require_scope('conversations:read'))],
)
async def list_conversations(
    auth: DostupUserAuth = Depends(require_user),
    info_service: AppConversationInfoService = _conversation_info_service_dep,
    limit: Annotated[int, Query(gt=0, le=100)] = 25,
    page_id: Annotated[str | None, Query()] = None,
) -> ConversationList:
    """Return at most ``limit`` recent conversations for the caller."""
    # ``info_service`` is already scoped to the current user via the
    # injector's user_context, so we do not need to re-filter by user_id.
    await auth.get_user_id()  # ensures auth was actually resolved
    page = await info_service.search_app_conversation_info(
        sort_order=AppConversationSortOrder.CREATED_AT_DESC,
        limit=limit,
        page_id=page_id,
    )
    return ConversationList(
        items=[_conversation_to_summary(c) for c in page.items],
        next_page_id=page.next_page_id,
    )


@router.get(
    '/conversations/{conversation_id}',
    summary='Get a single conversation summary',
    response_model=ConversationSummary,
    responses={404: {'description': 'Conversation not found.'}},
    dependencies=[Depends(require_scope('conversations:read'))],
)
async def get_conversation(
    conversation_id: UUID,
    auth: DostupUserAuth = Depends(require_user),
    service: AppConversationService = _conversation_service_dep,
) -> ConversationSummary:
    user_id = await auth.get_user_id()
    convo = await service.get_app_conversation(conversation_id)
    if convo is None or convo.created_by_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Conversation not found.',
        )
    return _conversation_to_summary(convo)


# ---------------------------------------------------------------------------
# Admin / introspection
# ---------------------------------------------------------------------------


@router.get(
    '/admin/ping',
    summary='Smoke test that the caller is an admin',
    response_model=dict,
    dependencies=[Depends(require_admin)],
    include_in_schema=False,
)
async def admin_ping() -> dict:
    return {'ok': True}


__all__ = ['router']
