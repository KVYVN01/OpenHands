"""Idempotency-Key middleware for DOSTUP_CRS POST endpoints.

Accepts an ``Idempotency-Key`` header on POST requests.  When present the
middleware checks for a previous response cached under the same
``(user_id, key)`` pair.  If found the cached response is replayed.
Otherwise the request is processed normally and the result stored for
24 hours (configurable via ``DOSTUP_IDEMPOTENCY_TTL_HOURS``).
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from openhands.app_server.user_auth.dostup.db import get_session_factory, init_models

logger = logging.getLogger(__name__)

_TTL_HOURS = int(os.getenv('DOSTUP_IDEMPOTENCY_TTL_HOURS', '24'))


async def _lookup(user_id: str, key: str) -> tuple[int, str] | None:
    """Return ``(status_code, response_body)`` if the key exists and has not expired."""
    await init_models()
    from sqlalchemy import select

    from openhands.app_server.user_auth.dostup.models import IdempotencyRecord

    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(IdempotencyRecord)
            .where(IdempotencyRecord.user_id == user_id)
            .where(IdempotencyRecord.idempotency_key == key)
            .where(IdempotencyRecord.expires_at > datetime.now(tz=timezone.utc))
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return row.status_code, row.response_body


async def _store(
    user_id: str,
    key: str,
    method: str,
    path: str,
    status_code: int,
    response_body: str,
) -> None:
    await init_models()
    from openhands.app_server.user_auth.dostup.models import IdempotencyRecord

    now = datetime.now(tz=timezone.utc)
    record = IdempotencyRecord(
        id=uuid.uuid4().hex,
        user_id=user_id,
        idempotency_key=key,
        method=method,
        path=path,
        status_code=status_code,
        response_body=response_body,
        created_at=now,
        expires_at=now + timedelta(hours=_TTL_HOURS),
    )
    factory = get_session_factory()
    async with factory() as session:
        async with session.begin():
            session.add(record)


def _get_user_id(request: Request) -> str | None:
    """Best-effort user-id extraction from a cookie JWT."""
    try:
        from openhands.app_server.user_auth.dostup.security import decode_token

        cookie = request.cookies.get('dostup_session')
        if cookie:
            payload = decode_token(cookie)
            if payload and 'sub' in payload:
                return str(payload['sub'])
        auth_header = request.headers.get('Authorization', '')
        if auth_header.lower().startswith('bearer ') and not auth_header.split(' ', 1)[
            1
        ].startswith('dostup_pk_'):
            payload = decode_token(auth_header.split(' ', 1)[1])
            if payload and 'sub' in payload:
                return str(payload['sub'])
    except Exception:  # noqa: BLE001
        pass
    return None


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Replay cached responses for POST requests carrying ``Idempotency-Key``."""

    _IDEMPOTENT_PATHS = (
        '/api/v1/app-conversations',
        '/api/v1/bot/keys',
    )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.method != 'POST':
            return await call_next(request)

        idem_key = request.headers.get('Idempotency-Key')
        if not idem_key:
            return await call_next(request)

        if not any(request.url.path.startswith(p) for p in self._IDEMPOTENT_PATHS):
            return await call_next(request)

        user_id = _get_user_id(request)
        if not user_id:
            return await call_next(request)

        cached = await _lookup(user_id, idem_key)
        if cached is not None:
            status_code, body_str = cached
            try:
                body = json.loads(body_str)
            except (json.JSONDecodeError, TypeError):
                body = body_str
            return JSONResponse(
                status_code=status_code,
                content=body,
                headers={'X-Idempotent-Replay': 'true'},
            )

        response = await call_next(request)

        # Buffer the response body so we can store it.
        body_chunks: list[bytes] = []
        body_iter = getattr(response, 'body_iterator', None)
        if body_iter is not None:
            async for chunk in body_iter:
                if isinstance(chunk, str):
                    body_chunks.append(chunk.encode('utf-8'))
                else:
                    body_chunks.append(chunk)
        body_bytes = b''.join(body_chunks)

        try:
            await _store(
                user_id=user_id,
                key=idem_key,
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                response_body=body_bytes.decode('utf-8', errors='replace'),
            )
        except Exception:  # noqa: BLE001
            logger.warning(
                'Failed to store idempotency key %s', idem_key, exc_info=True
            )

        return Response(
            content=body_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
