"""HTTP endpoints powering the DOSTUP_CRS multi-user auth flow."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from openhands.app_server.user_auth.dostup.dostup_user_auth import (
    DOSTUP_COOKIE_NAME,
    DostupUserAuth,
)
from openhands.app_server.user_auth.dostup.security import (
    cookie_max_age,
    issue_token,
)
from openhands.app_server.user_auth.dostup.store import (
    UserRecord,
    authenticate,
    count_users,
    create_user,
    get_user_by_email,
)

router = APIRouter(prefix='/auth', tags=['DostupAuth'])


class LoginPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class RegisterPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    display_name: str = Field(default='', max_length=160)


class PublicUser(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    is_admin: bool


def _to_public(record: UserRecord) -> PublicUser:
    return PublicUser(
        id=record.id,
        email=record.email,  # type: ignore[arg-type]
        display_name=record.display_name,
        is_admin=record.is_admin,
    )


def _set_cookie(response: Response, request: Request, token: str) -> None:
    is_https = request.url.scheme == 'https'
    response.set_cookie(
        key=DOSTUP_COOKIE_NAME,
        value=token,
        max_age=cookie_max_age(),
        httponly=True,
        samesite='lax',
        secure=is_https,
        path='/',
    )


def _registration_allowed() -> bool:
    return os.getenv('DOSTUP_DISABLE_REGISTRATION', 'false').lower() not in (
        '1',
        'true',
        'yes',
    )


@router.post('/register', status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterPayload, request: Request, response: Response
) -> PublicUser:
    """Create a new user account.

    The very first account is always allowed (so a fresh install can
    bootstrap) and is granted admin. Subsequent self-service registration
    can be disabled by setting ``DOSTUP_DISABLE_REGISTRATION=true``.
    """
    if not _registration_allowed():
        existing_users = await count_users()
        if existing_users > 0:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail='Registration is disabled.'
            )

    existing = await get_user_by_email(payload.email)
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail='A user with this email already exists.'
        )

    is_first_user = (await count_users()) == 0
    try:
        record = await create_user(
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
            is_admin=is_first_user,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token = issue_token(record.id, record.email)
    _set_cookie(response, request, token)
    return _to_public(record)


@router.post('/login')
async def login(
    payload: LoginPayload, request: Request, response: Response
) -> PublicUser:
    record = await authenticate(payload.email, payload.password)
    if record is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password.'
        )
    token = issue_token(record.id, record.email)
    _set_cookie(response, request, token)
    return _to_public(record)


@router.post('/logout')
async def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(DOSTUP_COOKIE_NAME, path='/')
    return {'ok': True}


@router.get('/me')
async def me(request: Request) -> PublicUser:
    auth = await DostupUserAuth.get_instance(request)
    user_id = await auth.get_user_id()
    if not user_id or not auth._user:  # noqa: SLF001
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail='Not authenticated.')
    return _to_public(auth._user)  # noqa: SLF001
