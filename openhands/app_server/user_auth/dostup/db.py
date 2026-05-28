"""Async SQLite engine shared by the DOSTUP_CRS auth layer."""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_DEFAULT_DB_PATH = './workspace/dostup_users.sqlite3'

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _resolve_db_path() -> str:
    """Pick a writable location for the SQLite file.

    Order:
      1. ``DOSTUP_DB_PATH`` (full file path).
      2. ``OH_DATA_DIR`` / ``dostup_users.sqlite3``.
      3. ``./workspace/dostup_users.sqlite3`` (matches existing storage roots).
    """
    explicit = os.getenv('DOSTUP_DB_PATH')
    if explicit:
        return explicit
    data_dir = os.getenv('OH_DATA_DIR')
    if data_dir:
        return str(Path(data_dir) / 'dostup_users.sqlite3')
    return _DEFAULT_DB_PATH


def _build_engine() -> AsyncEngine:
    db_path = _resolve_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    url = f'sqlite+aiosqlite:///{db_path}'
    return create_async_engine(url, echo=False, future=True)


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _session_factory


async def session_scope() -> AsyncIterator[AsyncSession]:
    """Async generator yielding a session inside a transaction."""
    factory = get_session_factory()
    async with factory() as session:
        async with session.begin():
            yield session


async def init_models() -> None:
    """Create tables on first use. Idempotent."""
    from openhands.app_server.user_auth.dostup.models import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
