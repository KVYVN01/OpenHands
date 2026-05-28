"""UserAuth implementation backed by the DOSTUP_CRS local user database."""

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import Request
from pydantic import SecretStr

from openhands.app_server import shared
from openhands.app_server.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.app_server.secrets.secrets_models import Secrets
from openhands.app_server.secrets.secrets_store import SecretsStore
from openhands.app_server.settings.settings_models import Settings
from openhands.app_server.settings.settings_store import SettingsStore
from openhands.app_server.user_auth.dostup.api_key_store import (
    ApiKeyRecord,
    resolve_api_key,
)
from openhands.app_server.user_auth.dostup.security import (
    API_KEY_PREFIX,
    decode_token,
)
from openhands.app_server.user_auth.dostup.store import (
    UserRecord,
    get_user_by_id,
)
from openhands.app_server.user_auth.user_auth import AuthType, UserAuth

DOSTUP_COOKIE_NAME = 'dostup_session'
API_KEY_HEADER = 'X-Api-Key'
DOSTUP_API_KEY_STATE_ATTR = 'dostup_api_key'


def _extract_bearer(request: Request) -> str | None:
    """Return the ``Authorization: Bearer <token>`` value, if any."""
    header = request.headers.get('Authorization')
    if header and header.lower().startswith('bearer '):
        return header.split(' ', 1)[1].strip()
    return None


def _extract_jwt_token(request: Request) -> str | None:
    """Return the session-cookie JWT or a bearer JWT (anything not an API key)."""
    cookie_token = request.cookies.get(DOSTUP_COOKIE_NAME)
    if cookie_token:
        return cookie_token
    bearer = _extract_bearer(request)
    if bearer and not bearer.startswith(f'{API_KEY_PREFIX}_'):
        return bearer
    return None


def _extract_api_key_token(request: Request) -> str | None:
    """Return the API-key token from a Bearer header or ``X-Api-Key``."""
    api_key_header = request.headers.get(API_KEY_HEADER)
    if api_key_header:
        return api_key_header.strip()
    bearer = _extract_bearer(request)
    if bearer and bearer.startswith(f'{API_KEY_PREFIX}_'):
        return bearer
    return None


@dataclass
class DostupUserAuth(UserAuth):
    """Resolve the current user from a signed JWT issued by ``auth_router``."""

    _user: UserRecord | None = None
    _settings: Settings | None = None
    _settings_store: SettingsStore | None = field(default=None)
    _secrets_store: SecretsStore | None = field(default=None)
    _secrets: Secrets | None = None
    _api_key: ApiKeyRecord | None = None
    _auth_type: AuthType | None = AuthType.COOKIE

    async def get_user_id(self) -> str | None:
        return self._user.id if self._user else None

    async def get_user_email(self) -> str | None:
        return self._user.email if self._user else None

    async def get_access_token(self) -> SecretStr | None:
        return None

    async def get_provider_tokens(self) -> PROVIDER_TOKEN_TYPE | None:
        secrets = await self.get_secrets()
        return secrets.provider_tokens if secrets else None

    async def get_user_settings_store(self) -> SettingsStore:
        store = self._settings_store
        if store:
            return store
        user_id = await self.get_user_id()
        store = await shared.SettingsStoreImpl.get_instance(user_id)
        if store is None:
            raise ValueError('Failed to get settings store instance')
        self._settings_store = store
        return store

    async def get_secrets_store(self) -> SecretsStore:
        store = self._secrets_store
        if store:
            return store
        user_id = await self.get_user_id()
        store = await shared.SecretsStoreImpl.get_instance(user_id)
        if store is None:
            raise ValueError('Failed to get secrets store instance')
        self._secrets_store = store
        return store

    async def get_secrets(self) -> Secrets | None:
        if self._secrets is not None:
            return self._secrets
        store = await self.get_secrets_store()
        self._secrets = await store.load()
        return self._secrets

    def get_auth_type(self) -> AuthType | None:
        return self._auth_type

    async def get_mcp_api_key(self) -> str | None:
        return None

    @property
    def api_key(self) -> ApiKeyRecord | None:
        """The API key used for this request, if any. ``None`` for cookie/JWT auth."""
        return self._api_key

    @classmethod
    async def get_instance(cls, request: Request) -> 'DostupUserAuth':
        """Resolve the current user.

        Order of precedence:

        1. ``X-Api-Key`` header or ``Authorization: Bearer dostup_pk_*`` →
           API-key store lookup. The resolved key is stashed on
           ``request.state`` so downstream code can read it.
        2. ``dostup_session`` cookie or ``Authorization: Bearer <jwt>`` →
           JWT decode.

        Returns an unauthenticated instance if neither path resolves a user.
        """
        instance = cls()

        api_key_token = _extract_api_key_token(request)
        if api_key_token:
            api_key = await resolve_api_key(api_key_token)
            if api_key is not None:
                record = await get_user_by_id(api_key.user_id)
                if record is not None and record.is_active:
                    instance._user = record
                    instance._api_key = api_key
                    instance._auth_type = AuthType.BEARER
                    try:
                        setattr(request.state, DOSTUP_API_KEY_STATE_ATTR, api_key)
                    except AttributeError:
                        # ``request.state`` is read-only in some test harnesses;
                        # the bot router falls back to re-reading the header.
                        pass
                    return instance

        jwt_token = _extract_jwt_token(request)
        if not jwt_token:
            return instance
        payload = decode_token(jwt_token)
        if not payload:
            return instance
        user_id = payload.get('sub')
        if not isinstance(user_id, str):
            return instance
        record = await get_user_by_id(user_id)
        if record is None or not record.is_active:
            return instance
        instance._user = record
        return instance

    @classmethod
    async def get_for_user(cls, user_id: str) -> 'DostupUserAuth':
        instance = cls()
        record = await get_user_by_id(user_id)
        if record is not None and record.is_active:
            instance._user = record
        return instance
