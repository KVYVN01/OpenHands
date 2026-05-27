"""Async data access for DOSTUP_CRS users."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select

from openhands.app_server.user_auth.dostup.db import get_session_factory, init_models
from openhands.app_server.user_auth.dostup.models import User
from openhands.app_server.user_auth.dostup.security import (
    generate_salt,
    hash_password,
    verify_password,
)


@dataclass(frozen=True)
class UserRecord:
    """Plain snapshot returned to callers (decoupled from the ORM session)."""

    id: str
    email: str
    display_name: str
    is_active: bool
    is_admin: bool


def _to_record(user: User) -> UserRecord:
    return UserRecord(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
    )


async def _ensure_tables() -> None:
    await init_models()


async def get_user_by_id(user_id: str) -> UserRecord | None:
    await _ensure_tables()
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return _to_record(user) if user else None


async def get_user_by_email(email: str) -> UserRecord | None:
    await _ensure_tables()
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        user = result.scalar_one_or_none()
        return _to_record(user) if user else None


async def count_users() -> int:
    await _ensure_tables()
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(select(User.id))
        return len(result.all())


async def create_user(
    email: str, password: str, display_name: str = '', is_admin: bool = False
) -> UserRecord:
    await _ensure_tables()
    if not email or '@' not in email:
        raise ValueError('email is required and must contain "@"')
    if not password or len(password) < 8:
        raise ValueError('password must be at least 8 characters long')

    salt = generate_salt()
    password_hash = hash_password(password, salt)
    user_id = uuid.uuid4().hex
    factory = get_session_factory()
    async with factory() as session:
        async with session.begin():
            user = User(
                id=user_id,
                email=email.lower().strip(),
                display_name=display_name.strip() or email.split('@')[0],
                password_hash=password_hash,
                password_salt=salt,
                is_admin=is_admin,
                is_active=True,
            )
            session.add(user)
        await session.refresh(user)
        return _to_record(user)


async def authenticate(email: str, password: str) -> UserRecord | None:
    await _ensure_tables()
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.password_salt, user.password_hash):
            return None
        return _to_record(user)
