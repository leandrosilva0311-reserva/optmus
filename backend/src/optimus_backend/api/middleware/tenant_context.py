import json
import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from optimus_backend.application.use_cases.resolve_tenant import ResolveTenantByApiKeyUseCase
from optimus_backend.core.request_context.context import reset_request_context, set_request_context
from optimus_backend.core.request_context.models import RequestContext
from optimus_backend.domain.ports import TenantRateLimiter

LOGGER = logging.getLogger("optimus.request")

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

_PUBLIC_PATHS = {"/docs", "/redoc", "/openapi.json", "/health", "/health/", "/auth/login", "/auth/logout"}


def _get_client_ip(request: Request) -> str:
    """Extract real client IP respecting Cloudflare and Nginx proxy headers."""
    cf_ip = request.headers.get("CF-Connecting-IP", "")
    if cf_ip:
        return cf_ip
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class TenantContextMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        resolver: ResolveTenantByApiKeyUseCase,
        tenant_rate_limiter: TenantRateLimiter,
        per_minute_limit: int,
    ) -> None:
        super().__init__(app)
        self._resolver = resolver
        self._tenant_rate_limiter = tenant_rate_limiter
        self._per_minute_limit = per_minute_limit

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _PUBLIC_PATHS:
            response = await call_next(request)
            for header, value in _SECURITY_HEADERS.items():
                response.headers[header] = value
            return response

        raw_api_key = request.headers.get("X-API-Key", "")
        if not raw_api_key:
            return JSONResponse(status_code=401, content={"detail": "missing api key"}, headers=_SECURITY_HEADERS)

        try:
            resolved = self._resolver.execute(raw_api_key)
        except PermissionError as exc:
            return JSONResponse(status_code=401, content={"detail": str(exc)}, headers=_SECURITY_HEADERS)

        if not self._tenant_rate_limiter.allow(resolved.tenant.id, limit=self._per_minute_limit):
            return JSONResponse(status_code=429, content={"detail": "tenant rate limit exceeded"}, headers=_SECURITY_HEADERS)

        context = RequestContext(
            execution_id=request.headers.get("X-Execution-Id", str(uuid4())),
            tenant_id=resolved.tenant.id,
            api_key_id=resolved.api_key.id,
            plan=resolved.tenant.plan,
            agent_id=request.headers.get("X-Agent-Id", "http"),
        )
        request.state.request_context = context
        request.state.client_ip = _get_client_ip(request)

        token = set_request_context(context)
        try:
            LOGGER.info(
                json.dumps(
                    {
                        "execution_id": context.execution_id,
                        "tenant_id": context.tenant_id,
                        "agent_id": context.agent_id,
                        "client_ip": request.state.client_ip,
                        "event_type": "request_received",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "data": {"path": request.url.path, "method": request.method},
                    }
                )
            )
            response = await call_next(request)
            for header, value in _SECURITY_HEADERS.items():
                response.headers[header] = value
            LOGGER.info(
                json.dumps(
                    {
                        "execution_id": context.execution_id,
                        "tenant_id": context.tenant_id,
                        "agent_id": context.agent_id,
                        "client_ip": request.state.client_ip,
                        "event_type": "request_completed",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "data": {"path": request.url.path, "status_code": response.status_code},
                    }
                )
            )
            return response
        finally:
            reset_request_context(token)
