"""SSE event stream and agent-server proxy endpoints for DOSTUP_CRS bots.

Provides:

* ``GET /api/v1/bot/conversations/{id}/events/stream`` — Server-Sent Events
  (SSE) stream that polls the event service and pushes new events to the
  client.  This eliminates the need for bots to open a direct WebSocket to
  the agent-server sandbox.

* ``GET /api/v1/bot/conversations/{id}/agent-server-url`` — Returns the
  agent-server URL for the given conversation so a bot can connect to the
  live WS / VSCode / PTY endpoints itself.

* ``GET /api/v1/bot/conversations/{id}/vscode-url`` — Proxied VSCode URL.

* ``GET /api/v1/bot/conversations/{id}/execution-status`` — Current
  execution status snapshot.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from openhands.app_server.app_conversation.app_conversation_service import (
    AppConversationService,
)
from openhands.app_server.bot_api.dependencies import require_user
from openhands.app_server.bot_api.scopes import require_scope
from openhands.app_server.config import (
    depends_app_conversation_service,
    depends_event_service,
)
from openhands.app_server.event.event_service import EventService
from openhands.app_server.user_auth.dostup.dostup_user_auth import DostupUserAuth

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/bot/conversations', tags=['Bot API — Streams'])

_conversation_service_dep = depends_app_conversation_service()
_event_service_dep = depends_event_service()


async def _resolve_conversation(
    conversation_id: UUID,
    auth: DostupUserAuth,
    service: AppConversationService,
):
    """Helper: fetch conversation and verify ownership."""
    user_id = await auth.get_user_id()
    convo = await service.get_app_conversation(conversation_id)
    if convo is None or convo.created_by_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Conversation not found.',
        )
    return convo


# ---------------------------------------------------------------------------
# SSE event stream
# ---------------------------------------------------------------------------


@router.get(
    '/{conversation_id}/events/stream',
    summary='SSE stream of conversation events',
    dependencies=[Depends(require_scope('conversations:read'))],
    responses={
        404: {'description': 'Conversation not found.'},
    },
)
async def event_stream(
    conversation_id: UUID,
    request: Request,
    auth: DostupUserAuth = Depends(require_user),
    service: AppConversationService = _conversation_service_dep,
    event_service: EventService = _event_service_dep,
    start_after: Annotated[str | None, Query()] = None,
) -> StreamingResponse:
    """Push conversation events as ``text/event-stream``.

    The stream emits ``data: <json>`` lines.  Each event carries the
    server-side ``page_id`` cursor so the client can pass it back as
    ``start_after`` on reconnect to resume from where it left off.

    The stream terminates when the client disconnects or after ~5 min
    of idle (no new events).
    """
    await _resolve_conversation(conversation_id, auth, service)

    async def _generate():
        cursor = start_after
        idle_ticks = 0
        max_idle = 300  # ~5 min at 1s interval
        while True:
            if await request.is_disconnected():
                break
            try:
                events_page = await event_service.search_events(
                    conversation_id=conversation_id,
                    page_id=cursor,
                    limit=50,
                )
                items = list(events_page.items) if events_page.items else []
                next_cursor = events_page.next_page_id
            except Exception:  # noqa: BLE001
                logger.debug(
                    'Event fetch failed for %s', conversation_id, exc_info=True
                )
                items = []
                next_cursor = None

            if items:
                idle_ticks = 0
                for evt in items:
                    evt_dict = (
                        evt.model_dump(mode='json')
                        if hasattr(evt, 'model_dump')
                        else (evt if isinstance(evt, dict) else {'data': str(evt)})
                    )
                    data = json.dumps(evt_dict, default=str)
                    yield f'data: {data}\n\n'
                if next_cursor:
                    cursor = next_cursor
            else:
                idle_ticks += 1
                yield ': heartbeat\n\n'

            if idle_ticks >= max_idle:
                yield 'event: timeout\ndata: {}\n\n'
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        _generate(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )


# ---------------------------------------------------------------------------
# Agent-server URL (for bots that want to connect WS directly)
# ---------------------------------------------------------------------------


@router.get(
    '/{conversation_id}/agent-server-url',
    summary='Get the agent-server URL for direct WS connection',
    dependencies=[Depends(require_scope('conversations:read'))],
    responses={404: {'description': 'Conversation not found.'}},
)
async def agent_server_url(
    conversation_id: UUID,
    auth: DostupUserAuth = Depends(require_user),
    service: AppConversationService = _conversation_service_dep,
) -> dict:
    """Return the agent-server URL so a bot can connect to live WS endpoints."""
    convo = await _resolve_conversation(conversation_id, auth, service)
    url = getattr(convo, 'agent_server_url', None)
    return {
        'conversation_id': str(conversation_id),
        'agent_server_url': url,
        'sandbox_id': convo.sandbox_id,
    }


# ---------------------------------------------------------------------------
# VSCode URL proxy
# ---------------------------------------------------------------------------


@router.get(
    '/{conversation_id}/vscode-url',
    summary='Get proxied VSCode URL for the sandbox',
    dependencies=[Depends(require_scope('conversations:read'))],
    responses={404: {'description': 'Conversation not found.'}},
)
async def vscode_url(
    conversation_id: UUID,
    auth: DostupUserAuth = Depends(require_user),
    service: AppConversationService = _conversation_service_dep,
) -> dict:
    """Return the VSCode URL for the sandbox associated with this conversation."""
    convo = await _resolve_conversation(conversation_id, auth, service)
    agent_url = getattr(convo, 'agent_server_url', None)
    vscode_endpoint = f'{agent_url}/api/vscode/url' if agent_url else None
    return {
        'conversation_id': str(conversation_id),
        'vscode_url': vscode_endpoint,
        'agent_server_url': agent_url,
    }


# ---------------------------------------------------------------------------
# Execution status snapshot
# ---------------------------------------------------------------------------


@router.get(
    '/{conversation_id}/execution-status',
    summary='Current execution status of the conversation agent',
    dependencies=[Depends(require_scope('conversations:read'))],
    responses={404: {'description': 'Conversation not found.'}},
)
async def execution_status(
    conversation_id: UUID,
    auth: DostupUserAuth = Depends(require_user),
    service: AppConversationService = _conversation_service_dep,
) -> dict:
    """Snapshot of the agent execution status — no live WS required."""
    convo = await _resolve_conversation(conversation_id, auth, service)
    return {
        'conversation_id': str(conversation_id),
        'sandbox_status': getattr(
            getattr(convo, 'sandbox_status', None), 'value', None
        ),
        'execution_status': getattr(
            getattr(convo, 'execution_status', None), 'value', None
        ),
        'agent_server_url': getattr(convo, 'agent_server_url', None),
    }


__all__ = ['router']
