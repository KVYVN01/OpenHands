"""Scope-enforcement helpers for DOSTUP_CRS bot API.

API keys carry a ``scopes`` field (e.g. ``conversations:read``,
``conversations:write``).  The ``require_scope`` dependency generator
validates that the calling key (or session-cookie, which is always
full-access) includes the required scope.

Usage in a router::

    @router.get(
        '/conversations',
        dependencies=[Depends(require_scope('conversations:read'))],
    )
    async def list_conversations(...):
        ...
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from openhands.app_server.bot_api.dependencies import require_user
from openhands.app_server.user_auth.dostup.api_key_store import ApiKeyRecord
from openhands.app_server.user_auth.dostup.dostup_user_auth import (
    DOSTUP_API_KEY_STATE_ATTR,
    DostupUserAuth,
)

KNOWN_SCOPES: set[str] = {
    'conversations:read',
    'conversations:write',
    'settings:read',
    'settings:write',
    'secrets:read',
    'secrets:write',
    'keys:manage',
    'admin',
}


def _get_active_scopes(request: Request, auth: DostupUserAuth) -> list[str]:
    """Return the effective scopes for the current request.

    Session-cookie auth is treated as full-access (all known scopes).
    API-key auth returns only the scopes stored on the key record.
    """
    api_key: ApiKeyRecord | None = auth.api_key
    if api_key is None:
        try:
            api_key = getattr(request.state, DOSTUP_API_KEY_STATE_ATTR, None)
        except AttributeError:
            pass

    if api_key is None:
        return list(KNOWN_SCOPES)

    if not api_key.scopes or api_key.scopes == ('',):
        return list(KNOWN_SCOPES)

    return list(api_key.scopes)


def require_scope(scope: str):
    """FastAPI dependency that enforces a specific scope on the request.

    Returns a dependency callable suitable for use in ``Depends(...)`` or
    in a route's ``dependencies=[...]`` list.
    """

    async def _check(
        request: Request,
        auth: DostupUserAuth = Depends(require_user),
    ) -> None:
        active = _get_active_scopes(request, auth)
        if scope not in active and 'admin' not in active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Missing required scope: {scope}',
            )

    return _check
