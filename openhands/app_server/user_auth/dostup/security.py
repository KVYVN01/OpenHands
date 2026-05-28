"""Password hashing and JWT helpers for DOSTUP_CRS auth.

We deliberately stick to ``hashlib`` + ``hmac`` + ``secrets`` from the
standard library so the auth layer adds no transitive crypto
dependencies on top of what OpenHands already ships.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt

_PBKDF2_ITERATIONS = 240_000
_PBKDF2_DIGEST = 'sha256'
_SALT_BYTES = 16
_JWT_ALG = 'HS256'
_JWT_TTL_SECONDS = 60 * 60 * 12  # 12h


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def _b64decode(value: str) -> bytes:
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def generate_salt() -> str:
    return _b64(secrets.token_bytes(_SALT_BYTES))


def hash_password(password: str, salt: str) -> str:
    """Return a PBKDF2-SHA256 hash of ``password`` using ``salt``."""
    if not password:
        raise ValueError('password must not be empty')
    raw = hashlib.pbkdf2_hmac(
        _PBKDF2_DIGEST,
        password.encode('utf-8'),
        _b64decode(salt),
        _PBKDF2_ITERATIONS,
    )
    return _b64(raw)


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Constant-time compare of a freshly-hashed password against the stored one."""
    if not password or not salt or not expected_hash:
        return False
    try:
        candidate = hash_password(password, salt)
    except ValueError:
        return False
    return hmac.compare_digest(candidate, expected_hash)


def _resolve_secret_path() -> Path:
    base = os.getenv('OH_DATA_DIR') or './workspace'
    return Path(base) / 'dostup_jwt.secret'


def _load_or_generate_secret() -> str:
    explicit = os.getenv('DOSTUP_JWT_SECRET')
    if explicit:
        return explicit
    path = _resolve_secret_path()
    if path.exists():
        return path.read_text().strip()
    path.parent.mkdir(parents=True, exist_ok=True)
    generated = secrets.token_urlsafe(48)
    path.write_text(generated)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return generated


_jwt_secret_cache: str | None = None


def get_jwt_secret() -> str:
    global _jwt_secret_cache
    if _jwt_secret_cache is None:
        _jwt_secret_cache = _load_or_generate_secret()
    return _jwt_secret_cache


def issue_token(user_id: str, email: str) -> str:
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        'sub': user_id,
        'email': email,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(seconds=_JWT_TTL_SECONDS)).timestamp()),
        'iss': 'dostup-crs',
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=_JWT_ALG)


def decode_token(token: str) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        return jwt.decode(token, get_jwt_secret(), algorithms=[_JWT_ALG])
    except jwt.PyJWTError:
        return None


def cookie_max_age() -> int:
    return _JWT_TTL_SECONDS


# ---------------------------------------------------------------------------
# API-key helpers
# ---------------------------------------------------------------------------
#
# Tokens are of the form
#
#     dostup_pk_<key_id>_<secret>
#
# where ``key_id`` is the row id stored in ``dostup_api_keys`` and
# ``secret`` is a 32-byte url-safe random string. The secret is hashed with
# PBKDF2 (per-key salt) on disk; only the hash is stored.

API_KEY_PREFIX = 'dostup_pk'
_API_KEY_SECRET_BYTES = 32


def generate_api_key_secret() -> str:
    """Return a url-safe random string suitable for use as a token secret."""
    return secrets.token_urlsafe(_API_KEY_SECRET_BYTES)


def format_api_key(key_id: str, secret: str) -> str:
    """Combine ``key_id`` + ``secret`` into the canonical wire format."""
    return f'{API_KEY_PREFIX}_{key_id}_{secret}'


def parse_api_key(token: str) -> tuple[str, str] | None:
    """Split a wire-format token into ``(key_id, secret)``.

    Returns ``None`` if the prefix or shape does not match.
    """
    if not token or not token.startswith(f'{API_KEY_PREFIX}_'):
        return None
    body = token[len(API_KEY_PREFIX) + 1 :]
    if '_' not in body:
        return None
    key_id, _, secret = body.partition('_')
    if not key_id or not secret:
        return None
    return key_id, secret


def hash_api_key_secret(secret: str, salt: str) -> str:
    """Hash a token secret using the same parameters as passwords."""
    if not secret:
        raise ValueError('secret must not be empty')
    raw = hashlib.pbkdf2_hmac(
        _PBKDF2_DIGEST,
        secret.encode('utf-8'),
        _b64decode(salt),
        _PBKDF2_ITERATIONS,
    )
    return _b64(raw)


def verify_api_key_secret(secret: str, salt: str, expected_hash: str) -> bool:
    """Constant-time compare of a token secret against the stored hash."""
    if not secret or not salt or not expected_hash:
        return False
    try:
        candidate = hash_api_key_secret(secret, salt)
    except ValueError:
        return False
    return hmac.compare_digest(candidate, expected_hash)
