from fastapi import APIRouter, Depends

from optimus_backend.api.authz import ensure_access
from optimus_backend.api.dependencies import get_current_user
from optimus_backend.core.auth_scopes import ADMIN_READ
from optimus_backend.schemas.agents import AgentCatalogItem

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/catalog", response_model=list[AgentCatalogItem])
def agent_catalog(user: dict[str, str] = Depends(get_current_user)) -> list[AgentCatalogItem]:
    ensure_access(user, {"admin", "operator", "viewer"}, {ADMIN_READ}, "/agents/catalog")
    return [
        AgentCatalogItem(
            key="dev_architect",
            title="DevArchitectAgent",
            responsibilities=["architecture analysis", "refactoring plan", "coupling diagnostics"],
        ),
        AgentCatalogItem(
            key="bug_hunter",
            title="BugHunterAgent",
            responsibilities=["failure triage", "root-cause hypotheses", "patch proposal"],
        ),
        AgentCatalogItem(
            key="qa",
            title="QAAgent",
            responsibilities=["smoke plan", "regression checks", "validation report"],
        ),
        AgentCatalogItem(
            key="ops_sentinel",
            title="OpsSentinelAgent",
            responsibilities=["health checks", "config risk analysis", "runtime diagnostics"],
        ),
        AgentCatalogItem(
            key="analyst",
            title="AnalystAgent",
            responsibilities=["technical summary", "executive summary", "bottleneck highlights"],
        ),
    ]
