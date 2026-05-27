import contextlib
import os
import warnings

from fastapi.routing import Mount

with warnings.catch_warnings():
    warnings.simplefilter('ignore')

from fastapi import (
    FastAPI,
    Request,
)
from fastapi.responses import JSONResponse

from openhands.app_server import v1_router
from openhands.app_server.config import get_app_lifespan_service
from openhands.app_server.integrations.service_types import AuthenticationError
from openhands.app_server.mcp.mcp_router import init_tavily_proxy, mcp_server
from openhands.app_server.middleware import (
    CacheControlMiddleware,
    InMemoryRateLimiter,
    LocalhostCORSMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
)
from openhands.app_server.static import SPAStaticFiles
from openhands.app_server.status.status_router import router as health_router
from openhands.app_server.version import get_version

# Initialize the Tavily MCP proxy before creating the app
init_tavily_proxy()

mcp_app = mcp_server.http_app(path='/mcp', stateless_http=True)


def combine_lifespans(*lifespans):
    # Create a combined lifespan to manage multiple session managers
    @contextlib.asynccontextmanager
    async def combined_lifespan(app):
        async with contextlib.AsyncExitStack() as stack:
            for lifespan in lifespans:
                await stack.enter_async_context(lifespan(app))
            yield

    return combined_lifespan


lifespans = [mcp_app.lifespan]
app_lifespan_ = get_app_lifespan_service()
if app_lifespan_:
    lifespans.append(app_lifespan_.lifespan)


from openhands.app_server.shared import server_config as _server_config  # noqa: E402
from openhands.app_server.types import AppMode as _AppMode  # noqa: E402

_is_dostup = getattr(_server_config, 'app_mode', None) == _AppMode.DOSTUP  # type: ignore[attr-defined]
_app_title = 'DOSTUP_CRS' if _is_dostup else 'OpenHands'
_app_description = (
    (
        'DOSTUP_CRS — multi-user OpenHands-based agent server. '
        'See `/api/v1/auth/*` for browser auth, `/api/v1/bot/*` for the bot '
        'API, and `/api/v1/bot/keys` to issue API keys.'
    )
    if _is_dostup
    else 'OpenHands: Code Less, Make More'
)

app = FastAPI(
    title=_app_title,
    description=_app_description,
    version=get_version(),
    lifespan=combine_lifespans(*lifespans),
    routes=[Mount(path='/mcp', app=mcp_app)],
)


def _custom_openapi() -> dict:
    """Inject DOSTUP_CRS-aware security schemes into the OpenAPI document."""
    if getattr(app, '_openapi_schema_cached', None) is not None:
        return app._openapi_schema_cached  # type: ignore[attr-defined]

    from fastapi.openapi.utils import get_openapi

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault('components', {}).setdefault('securitySchemes', {}).update(
        {
            'DostupSessionCookie': {
                'type': 'apiKey',
                'in': 'cookie',
                'name': 'dostup_session',
                'description': (
                    'Set by `POST /api/v1/auth/login` and `POST /api/v1/auth/register`. '
                    'Used by the React frontend.'
                ),
            },
            'DostupApiKey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-Api-Key',
                'description': (
                    'Long-lived bot token created via '
                    '`POST /api/v1/bot/keys`. Can also be sent as '
                    '`Authorization: Bearer dostup_pk_...`.'
                ),
            },
            'DostupBearer': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT-or-dostup_pk',
                'description': (
                    'Either a session JWT (rare) or a bot API key. '
                    'Prefer `X-Api-Key` for bots.'
                ),
            },
        }
    )
    app._openapi_schema_cached = schema  # type: ignore[attr-defined]
    return schema


app.openapi = _custom_openapi  # type: ignore[method-assign]


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    request_id = getattr(getattr(request, 'state', None), 'request_id', None)
    body: dict = {
        'error': {
            'code': 'authentication_error',
            'message': str(exc),
        }
    }
    if request_id:
        body['error']['request_id'] = request_id
    return JSONResponse(status_code=401, content=body)


from fastapi.exceptions import RequestValidationError  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402


@app.exception_handler(StarletteHTTPException)
async def structured_http_error_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Wrap every HTTP error in the unified ``{error: {code, message, ...}}`` envelope."""
    from typing import Any

    request_id = getattr(getattr(request, 'state', None), 'request_id', None)
    detail: Any = exc.detail
    status_map = {
        400: 'bad_request',
        401: 'unauthorized',
        403: 'forbidden',
        404: 'not_found',
        409: 'conflict',
        422: 'validation_error',
        429: 'rate_limited',
    }
    code = status_map.get(exc.status_code, f'http_{exc.status_code}')
    message = str(detail) if detail else f'HTTP {exc.status_code}'
    details: dict | None = None
    body: dict = {'error': {'code': code, 'message': message}}
    if details:
        body['error']['details'] = details
    if request_id:
        body['error']['request_id'] = request_id
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def structured_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Turn Pydantic 422s into the unified error envelope."""
    request_id = getattr(getattr(request, 'state', None), 'request_id', None)
    body: dict = {
        'error': {
            'code': 'validation_error',
            'message': 'Request validation failed.',
            'details': {'errors': exc.errors()},
        }
    }
    if request_id:
        body['error']['request_id'] = request_id
    return JSONResponse(status_code=422, content=body)


app.include_router(v1_router.router)
app.include_router(health_router)

# SaaS-compat stubs (only in DOSTUP mode)
if _is_dostup:
    from openhands.app_server.bot_api.compat_router import (  # noqa: E402
        router as _compat_router,
    )

    app.include_router(_compat_router)

# Middleware and static file setup (merged from listen.py)
if os.getenv('SERVE_FRONTEND', 'true').lower() == 'true':
    # Try standard build/ first, then build/client/ (Windows EPERM fallback)
    build_dir = None
    for candidate in ('./frontend/build', './frontend/build/client'):
        if os.path.isdir(candidate) and os.path.isfile(
            os.path.join(candidate, 'index.html')
        ):
            build_dir = candidate
            break
    if build_dir:
        app.mount(
            '/', SPAStaticFiles(directory=build_dir, html=True), name='dist'
        )

app.add_middleware(LocalhostCORSMiddleware)
app.add_middleware(CacheControlMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=InMemoryRateLimiter(requests=10, seconds=1),
)

if _is_dostup:
    from openhands.app_server.bot_api.idempotency import (  # noqa: E402
        IdempotencyMiddleware,
    )

    app.add_middleware(IdempotencyMiddleware)
