"""DOSTUP_CRS API-key management endpoints.

These endpoints power the *issuing* side of bot tokens. Authentication
is intentionally restricted to a real browser session — see
``require_session_user`` — so that a leaked API key cannot mint more
keys for itself.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from openhands.app_server.bot_api.dependencies import (
    require_session_user,
)
from openhands.app_server.bot_api.schemas import (
    ApiKeyInfo,
    ApiKeyList,
    CreateApiKeyRequest,
    CreateApiKeyResponse,
)
from openhands.app_server.user_auth.dostup.api_key_store import (
    ApiKeyRecord,
    create_api_key,
    list_api_keys,
    revoke_api_key,
)
from openhands.app_server.user_auth.dostup.dostup_user_auth import DostupUserAuth

router = APIRouter(prefix='/bot/keys', tags=['Bot API'])


def _to_info(record: ApiKeyRecord) -> ApiKeyInfo:
    return ApiKeyInfo(
        id=record.id,
        name=record.name,
        prefix=record.prefix,
        scopes=list(record.scopes),
        created_at=record.created_at,
        expires_at=record.expires_at,
        last_used_at=record.last_used_at,
        revoked_at=record.revoked_at,
        is_active=record.is_active,
    )


@router.get('', summary="List the caller's API keys", response_model=ApiKeyList)
async def list_keys(
    auth: DostupUserAuth = Depends(require_session_user),
) -> ApiKeyList:
    user_id = await auth.get_user_id()
    assert user_id is not None
    records = await list_api_keys(user_id)
    return ApiKeyList(items=[_to_info(r) for r in records])


@router.post(
    '',
    summary='Create a new API key',
    status_code=status.HTTP_201_CREATED,
    response_model=CreateApiKeyResponse,
    responses={
        400: {'description': 'Invalid request body.'},
        401: {'description': 'Authentication required.'},
        403: {'description': 'API keys cannot mint other API keys.'},
    },
)
async def create_key(
    payload: CreateApiKeyRequest,
    request: Request,
    auth: DostupUserAuth = Depends(require_session_user),
) -> CreateApiKeyResponse:
    user_id = await auth.get_user_id()
    assert user_id is not None
    try:
        issued = await create_api_key(
            user_id=user_id,
            name=payload.name,
            scopes=tuple(payload.scopes),
            expires_at=payload.expires_at,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return CreateApiKeyResponse(key=_to_info(issued.record), token=issued.token)


@router.delete(
    '/{key_id}',
    summary='Revoke an API key',
    responses={404: {'description': 'Key not found or already revoked.'}},
)
async def delete_key(
    key_id: str,
    auth: DostupUserAuth = Depends(require_session_user),
) -> dict[str, bool]:
    user_id = await auth.get_user_id()
    assert user_id is not None
    revoked = await revoke_api_key(user_id, key_id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='API key not found.',
        )
    return {'ok': True}


__all__ = ['router']
