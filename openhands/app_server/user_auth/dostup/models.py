"""SQLAlchemy ORM models backing DOSTUP_CRS multi-user auth."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'dostup_users'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160), default='')
    password_hash: Mapped[str] = mapped_column(String(512))
    password_salt: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    def to_public_dict(self) -> dict:
        return {
            'id': self.id,
            'email': self.email,
            'display_name': self.display_name,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
        }


class IdempotencyRecord(Base):
    """Stores idempotency keys so retried POST requests return the same response."""

    __tablename__ = 'dostup_idempotency'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(256), index=True)
    method: Mapped[str] = mapped_column(String(8))
    path: Mapped[str] = mapped_column(String(512))
    status_code: Mapped[int] = mapped_column(default=200)
    response_body: Mapped[str] = mapped_column(String(65536), default='')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )


class ApiKey(Base):
    """Long-lived API key issued to a user for bot / programmatic access.

    The plaintext token (``dostup_pk_<id>_<secret>``) is only ever returned
    once at creation time; only a PBKDF2 hash of the secret half is stored.
    """

    __tablename__ = 'dostup_api_keys'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey('dostup_users.id'), index=True
    )
    name: Mapped[str] = mapped_column(String(160), default='')
    prefix: Mapped[str] = mapped_column(String(16))
    token_hash: Mapped[str] = mapped_column(String(512))
    token_salt: Mapped[str] = mapped_column(String(128))
    scopes: Mapped[str] = mapped_column(String(512), default='')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
