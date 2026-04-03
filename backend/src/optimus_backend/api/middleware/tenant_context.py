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
        if request.url.path in {"/docs", "/redoc", "/openapi.json", "/health", "/health/", "/auth/login", "/auth/logout"}:
            return await call_next(request)

        raw_api_key = request.headers.get("X-API-Key", "")
        if not raw_api_key:
            return JSONResponse(status_code=401, content={"detail": "missing api key"})

        try:
            resolved = self._resolver.execute(raw_api_key)
        except PermissionError as exc:
            return JSONResponse(status_code=401, content={"detail": str(exc)})

        if not self._tenant_rate_limiter.allow(resolved.tenant.id, limit=self._per_minute_limit):
            return JSONResponse(status_code=429, content={"detail": "tenant rate limit exceeded"})

        context = RequestContext(
            execution_id=request.headers.get("X-Execution-Id", str(uuid4())),
            tenant_id=resolved.tenant.id,
            api_key_id=resolved.api_key.id,
            plan=resolved.tenant.plan,
            agent_id=request.headers.get("X-Agent-Id", "http"),
        )
        request.state.request_context = context

        token = set_request_context(context)
        try:
            LOGGER.info(
                json.dumps(
                    {
                        "execution_id": context.execution_id,
                        "tenant_id": context.tenant_id,
                        "agent_id": context.agent_id,
                        "event_type": "request_received",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "data": {"path": request.url.path, "method": request.method},
                    }
                )
            )
            response = await call_next(request)
            LOGGER.info(
                json.dumps(
                    {
                        "execution_id": context.execution_id,
                        "tenant_id": context.tenant_id,
                        "agent_id": context.agent_id,
                        "event_type": "request_completed",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "data": {"path": request.url.path, "status_code": response.status_code},
                    }
                )
            )
            return response
        finally:
            reset_request_context(token)
