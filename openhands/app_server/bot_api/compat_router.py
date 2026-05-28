"""SaaS-compatibility stub endpoints for DOSTUP_CRS mode.

When the server runs in ``dostup`` mode these endpoints return
structured "not applicable" responses so that bots and integrations
built for the SaaS surface get a clear signal instead of 404.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=['DOSTUP Compat'])

_NOT_APPLICABLE = {
    'error': {
        'code': 'not_applicable',
        'message': (
            'This endpoint belongs to the SaaS deployment and is not '
            'available in DOSTUP_CRS mode.'
        ),
    }
}


def _stub_response() -> JSONResponse:
    return JSONResponse(status_code=501, content=_NOT_APPLICABLE)


@router.api_route(
    '/api/authenticate',
    methods=['GET', 'POST'],
    summary='SaaS auth (not available in DOSTUP mode)',
    include_in_schema=False,
)
async def authenticate_stub(request: Request) -> JSONResponse:
    return _stub_response()


@router.api_route(
    '/api/keycloak/callback',
    methods=['GET', 'POST'],
    summary='Keycloak callback (not available in DOSTUP mode)',
    include_in_schema=False,
)
async def keycloak_callback_stub(request: Request) -> JSONResponse:
    return _stub_response()


@router.api_route(
    '/api/unset-provider-tokens',
    methods=['POST'],
    include_in_schema=False,
)
async def unset_provider_tokens_stub(request: Request) -> JSONResponse:
    return _stub_response()


@router.api_route(
    '/api/keys',
    methods=['GET', 'POST', 'DELETE'],
    include_in_schema=False,
)
async def legacy_keys_stub(request: Request) -> JSONResponse:
    return _stub_response()


@router.api_route(
    '/api/organizations/{path:path}',
    methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
    include_in_schema=False,
)
async def organizations_stub(request: Request, path: str = '') -> JSONResponse:
    return _stub_response()


@router.api_route(
    '/api/email/{path:path}',
    methods=['GET', 'POST'],
    include_in_schema=False,
)
async def email_stub(request: Request, path: str = '') -> JSONResponse:
    return _stub_response()


@router.api_route(
    '/api/billing/{path:path}',
    methods=['GET', 'POST', 'PUT', 'DELETE'],
    include_in_schema=False,
)
async def billing_stub(request: Request, path: str = '') -> JSONResponse:
    return _stub_response()


@router.api_route(
    '/api/features',
    methods=['GET'],
    include_in_schema=False,
)
async def features_stub(request: Request) -> JSONResponse:
    return _stub_response()


@router.api_route(
    '/api/security/{path:path}',
    methods=['GET', 'POST', 'PUT', 'DELETE'],
    include_in_schema=False,
)
async def security_stub(request: Request, path: str = '') -> JSONResponse:
    return _stub_response()


__all__ = ['router']
