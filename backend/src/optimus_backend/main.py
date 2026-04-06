from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from optimus_backend.api.dependencies import get_tenant_rate_limiter, get_tenant_resolver_use_case
from optimus_backend.api.middleware.tenant_context import TenantContextMiddleware
from optimus_backend.api.routes.agents import router as agents_router
from optimus_backend.api.routes.auth import router as auth_router
from optimus_backend.api.routes.executions import router as executions_router
from optimus_backend.api.routes.health import router as health_router
from optimus_backend.api.routes.scenarios import router as scenarios_router
from optimus_backend.settings.config import config

_docs_url = "/docs" if config.docs_enabled else None
_redoc_url = "/redoc" if config.docs_enabled else None
_openapi_url = "/openapi.json" if config.docs_enabled else None

app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)
# TrustedHostMiddleware runs outermost — rejects requests with invalid Host header before any processing
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.optimumprime.org", "localhost", "127.0.0.1"],
)
app.add_middleware(
    TenantContextMiddleware,
    resolver=get_tenant_resolver_use_case(),
    tenant_rate_limiter=get_tenant_rate_limiter(),
    per_minute_limit=config.rate_limit_tenant_per_minute,
)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(executions_router)
app.include_router(agents_router)
app.include_router(scenarios_router)
