import asyncio
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from urllib.parse import urlparse

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
from starlette.types import ASGIApp

from openhands.app_server.config import get_global_config


class LocalhostCORSMiddleware(CORSMiddleware):
    """Custom CORS middleware that allows any request from localhost/127.0.0.1 domains,
    while using standard CORS rules for other origins.
    """

    def __init__(self, app: ASGIApp) -> None:
        config = get_global_config()
        allow_origins = tuple(config.permitted_cors_origins)
        super().__init__(
            app,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )

    def is_allowed_origin(self, origin: str) -> bool:
        if origin and not self.allow_origins and not self.allow_origin_regex:
            parsed = urlparse(origin)
            hostname = parsed.hostname or ''

            # Allow any localhost/127.0.0.1 origin regardless of port
            if hostname in ['localhost', '127.0.0.1']:
                return True

            # Allow any origin when no specific origins are configured (development mode)
            # WARNING: This disables CORS protection. Use explicit CORS origins in production.
            logging.getLogger(__name__).warning(
                f'No CORS origins configured, allowing origin: {origin}. '
                'Set OH_PERMITTED_CORS_ORIGINS for production environments.'
            )
            return True

        # For missing origin or other origins, use the parent class's logic
        result: bool = super().is_allowed_origin(origin)
        return result


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Middleware to disable caching for all routes by adding appropriate headers"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        if request.url.path.startswith('/assets'):
            # The content of the assets directory has fingerprinted file names so we cache aggressively
            response.headers['Cache-Control'] = 'public, max-age=2592000, immutable'
        else:
            response.headers['Cache-Control'] = (
                'no-cache, no-store, must-revalidate, max-age=0'
            )
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject ``X-Request-Id`` into every request/response.

    If the client already sent the header, it is preserved (forwarded).
    Otherwise a UUID-4 is generated. The id is stashed on
    ``request.state.request_id`` for use by downstream handlers.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get('X-Request-Id') or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers['X-Request-Id'] = request_id
        return response


# ---------------------------------------------------------------------------
# Rate limiting (per-user when authenticated, per-IP fallback)
# ---------------------------------------------------------------------------


def _rate_limit_key(request: Request) -> str:
    """Return ``user_id`` if the request is authenticated, else client IP."""
    user_id = getattr(getattr(request, 'state', None), 'rate_limit_user_id', None)
    if user_id:
        return f'user:{user_id}'
    host = request.client.host if request.client else '0.0.0.0'
    return f'ip:{host}'


class InMemoryRateLimiter:
    history: dict[str, list[datetime]]
    requests: int
    seconds: int
    sleep_seconds: int

    def __init__(self, requests: int = 2, seconds: int = 1, sleep_seconds: int = 1):
        self.requests = requests
        self.seconds = seconds
        self.sleep_seconds = sleep_seconds
        self.history = defaultdict(list)
        self.sleep_seconds = sleep_seconds

    def _clean_old_requests(self, key: str) -> None:
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.seconds)
        self.history[key] = [ts for ts in self.history[key] if ts > cutoff]

    async def __call__(self, request: Request) -> bool:
        key = _rate_limit_key(request)
        now = datetime.now()

        self._clean_old_requests(key)

        self.history[key].append(now)

        if len(self.history[key]) > self.requests * 2:
            return False
        elif len(self.history[key]) > self.requests:
            if self.sleep_seconds > 0:
                await asyncio.sleep(self.sleep_seconds)
                return True
            else:
                return False

        return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, rate_limiter: InMemoryRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not self.is_rate_limited_request(request):
            return await call_next(request)

        # Attempt lightweight user-id extraction for per-user keying.
        self._try_set_user_id(request)

        ok = await self.rate_limiter(request)
        if not ok:
            request_id = getattr(getattr(request, 'state', None), 'request_id', None)
            body: dict = {
                'error': {
                    'code': 'rate_limited',
                    'message': 'Too many requests. Please retry later.',
                }
            }
            if request_id:
                body['error']['request_id'] = request_id
            return JSONResponse(
                status_code=429,
                content=body,
                headers={'Retry-After': '1'},
            )
        return await call_next(request)

    def is_rate_limited_request(self, request: StarletteRequest) -> bool:
        if request.url.path.startswith('/assets'):
            return False
        return True

    @staticmethod
    def _try_set_user_id(request: Request) -> None:
        """Best-effort extraction of an authenticated user id for keying.

        We peek at the cookie / API-key header without doing a full auth
        round-trip — the goal is just to differentiate users for rate-limit
        bucketing, not to enforce auth (that is the endpoint's job).
        """
        try:
            from openhands.app_server.user_auth.dostup.security import decode_token

            cookie = request.cookies.get('dostup_session')
            if cookie:
                payload = decode_token(cookie)
                if payload and 'sub' in payload:
                    request.state.rate_limit_user_id = payload['sub']
        except Exception:  # noqa: BLE001
            pass
