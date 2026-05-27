"""Dependencies shared by Bot API routes."""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from openhands.app_server.bot_api.schemas import BotIdentity
from openhands.app_server.user_auth.dostup.api_key_store import ApiKeyRecord
from openhands.app_server.user_auth.dostup.dostup_user_auth import (
    DOSTUP_API_KEY_STATE_ATTR,
    DostupUserAuth,
)


async def get_dostup_auth(request: Request) -> DostupUserAuth:
    """Resolve a :class:`DostupUserAuth` for the current request.

    This is the bot-API entry point: it always uses the DOSTUP user-auth
    class regardless of the global ``user_auth_class`` setting, so the bot
    API is usable even when the server is otherwise running in OSS mode.
    """
    cached = getattr(request.state, 'user_auth', None)
    if isinstance(cached, DostupUserAuth):
        return cached
    auth = await DostupUserAuth.get_instance(request)
    try:
        request.state.user_auth = auth
    except AttributeError:
        pass
    return auth


async def require_user(request: Request) -> DostupUserAuth:
    """Authenticated dependency. 401s when no user is resolved."""
    auth = await get_dostup_auth(request)
    user_id = await auth.get_user_id()
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authentication required.',
        )
    return auth


async def require_admin(request: Request) -> DostupUserAuth:
    """Authenticated + admin-only dependency."""
    auth = await require_user(request)
    if not auth._user or not auth._user.is_admin:  # noqa: SLF001
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Admin privileges required.',
        )
    return auth


async def require_session_user(request: Request) -> DostupUserAuth:
    """Require a *browser* session — i.e. an actual logged-in human.

    API-key tokens are explicitly rejected. We use this for key-management
    endpoints so that a leaked API key cannot mint new API keys.
    """
    auth = await require_user(request)
    if auth.api_key is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                'API keys cannot manage other API keys. '
                'Use a logged-in browser session.'
            ),
        )
    return auth


def _api_key_from_state(request: Request) -> ApiKeyRecord | None:
    try:
        return getattr(request.state, DOSTUP_API_KEY_STATE_ATTR, None)
    except AttributeError:
        return None


async def build_identity(request: Request, auth: DostupUserAuth) -> BotIdentity:
    """Build a public :class:`BotIdentity` response from an authed ``auth``."""
    user = auth._user  # noqa: SLF001
    assert user is not None, 'require_user must run first'
    api_key = auth.api_key or _api_key_from_state(request)
    return BotIdentity(
        user_id=user.id,
        email=user.email,  # type: ignore[arg-type]
        display_name=user.display_name,
        is_admin=user.is_admin,
        auth_type='bearer' if api_key is not None else 'cookie',
        api_key_id=api_key.id if api_key else None,
        scopes=list(api_key.scopes) if api_key else [],
    )
