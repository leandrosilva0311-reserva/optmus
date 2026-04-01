from fastapi import FastAPI

from optimus_backend.api.routes.agents import router as agents_router
from optimus_backend.api.routes.auth import router as auth_router
from optimus_backend.api.routes.executions import router as executions_router
from optimus_backend.api.routes.health import router as health_router
from optimus_backend.api.routes.scenarios import router as scenarios_router
from optimus_backend.settings.config import config

app = FastAPI(title=config.app_name, version=config.app_version)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(executions_router)
app.include_router(agents_router)
app.include_router(scenarios_router)
