"""Async data access for DOSTUP_CRS API keys.

API keys are the long-lived credential a bot uses to talk to the server.
They live in the same SQLite database as the user table and are linked to
the issuing user via a foreign key.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select, update

from openhands.app_server.user_auth.dostup.db import (
    get_session_factory,
    init_models,
)
from openhands.app_server.user_auth.dostup.models import ApiKey
from openhands.app_server.user_auth.dostup.security import (
    format_api_key,
    generate_api_key_secret,
    generate_salt,
    hash_api_key_secret,
    parse_api_key,
    verify_api_key_secret,
)


@dataclass(frozen=True)
class ApiKeyRecord:
    """Plain snapshot returned to callers."""

    id: str
    user_id: str
    name: str
    prefix: str
    scopes: tuple[str, ...]
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None

    @property
    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and self.expires_at <= datetime.now(
            tz=timezone.utc
        ):
            return False
        return True


def _to_record(row: ApiKey) -> ApiKeyRecord:
    return ApiKeyRecord(
        id=row.id,
        user_id=row.user_id,
        name=row.name,
        prefix=row.prefix,
        scopes=tuple(s for s in (row.scopes or '').split(',') if s),
        created_at=row.created_at,
        expires_at=row.expires_at,
        last_used_at=row.last_used_at,
        revoked_at=row.revoked_at,
    )


async def _ensure_tables() -> None:
    await init_models()


@dataclass(frozen=True)
class IssuedApiKey:
    """Returned by :func:`create_api_key` so callers can display the secret once."""

    record: ApiKeyRecord
    token: str


async def create_api_key(
    user_id: str,
    name: str,
    scopes: tuple[str, ...] = (),
    expires_at: datetime | None = None,
) -> IssuedApiKey:
    """Create a new API key for ``user_id`` and return ``(record, plaintext token)``."""
    await _ensure_tables()
    name = (name or '').strip()
    if not name:
        raise ValueError('name must not be empty')
    if len(name) > 160:
        raise ValueError('name must be at most 160 characters')
    for scope in scopes:
        if not scope or ',' in scope or len(scope) > 64:
            raise ValueError(f'invalid scope: {scope!r}')

    key_id = uuid.uuid4().hex
    secret = generate_api_key_secret()
    salt = generate_salt()
    token_hash = hash_api_key_secret(secret, salt)
    prefix = secret[:8]
    token = format_api_key(key_id, secret)

    factory = get_session_factory()
    async with factory() as session:
        async with session.begin():
            row = ApiKey(
                id=key_id,
                user_id=user_id,
                name=name,
                prefix=prefix,
                token_hash=token_hash,
                token_salt=salt,
                scopes=','.join(scopes),
                expires_at=expires_at,
            )
            session.add(row)
        await session.refresh(row)
        record = _to_record(row)
    return IssuedApiKey(record=record, token=token)


async def list_api_keys(user_id: str) -> list[ApiKeyRecord]:
    """Return the user's API keys (active + revoked) ordered by creation time."""
    await _ensure_tables()
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(ApiKey)
            .where(ApiKey.user_id == user_id)
            .order_by(ApiKey.created_at.desc())
        )
        return [_to_record(row) for row in result.scalars().all()]


async def revoke_api_key(user_id: str, key_id: str) -> bool:
    """Mark a key as revoked. Returns True if a key was changed."""
    await _ensure_tables()
    now = datetime.now(tz=timezone.utc)
    factory = get_session_factory()
    async with factory() as session:
        async with session.begin():
            result = await session.execute(
                update(ApiKey)
                .where(ApiKey.id == key_id)
                .where(ApiKey.user_id == user_id)
                .where(ApiKey.revoked_at.is_(None))
                .values(revoked_at=now)
            )
        # ``CursorResult.rowcount`` is dynamically attached; ``Result`` does
        # not declare it in the type stubs, so coerce via ``getattr``.
        return int(getattr(result, 'rowcount', 0) or 0) > 0


async def resolve_api_key(token: str) -> ApiKeyRecord | None:
    """Look up an API key by its wire-format token.

    Returns ``None`` if the token cannot be parsed, is unknown, or is no
    longer active. On success, updates ``last_used_at`` to *now*.
    """
    parsed = parse_api_key(token)
    if parsed is None:
        return None
    key_id, secret = parsed

    await _ensure_tables()
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(select(ApiKey).where(ApiKey.id == key_id))
        row = result.scalar_one_or_none()
        if row is None:
            return None
        if not verify_api_key_secret(secret, row.token_salt, row.token_hash):
            return None
        record = _to_record(row)
        if not record.is_active:
            return None
        # touch last_used_at; ignore failures so a read-only DB still authn's
        try:
            async with session.begin():
                await session.execute(
                    update(ApiKey)
                    .where(ApiKey.id == row.id)
                    .values(last_used_at=datetime.now(tz=timezone.utc))
                )
        except Exception:
            pass
    return record
