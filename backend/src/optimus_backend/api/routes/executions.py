from fastapi import APIRouter, Depends, HTTPException

from optimus_backend.api.dependencies import get_current_user, get_list_execution_use_case, get_start_execution_use_case
from optimus_backend.application.use_cases.list_executions import ListExecutionsUseCase
from optimus_backend.application.use_cases.start_execution import StartExecutionUseCase
from optimus_backend.schemas.execution import AuditEventView, ExecutionView, QueueTaskResponse, TaskRequest

router = APIRouter(prefix="/executions", tags=["executions"])


def ensure_role(user: dict[str, str], allowed: set[str]) -> None:
    if user["role"] not in allowed:
        raise HTTPException(status_code=403, detail="insufficient role")


@router.post("/run", response_model=QueueTaskResponse)
def run_execution(
    payload: TaskRequest,
    start: StartExecutionUseCase = Depends(get_start_execution_use_case),
    user: dict[str, str] = Depends(get_current_user),
) -> QueueTaskResponse:
    ensure_role(user, {"admin", "operator"})
    record = start.execute(project_id=payload.project_id, objective=payload.objective, agent=payload.agent)
    return QueueTaskResponse(execution_id=record.id, status=record.status)


@router.get("/", response_model=list[ExecutionView])
def list_executions(
    use_case: ListExecutionsUseCase = Depends(get_list_execution_use_case),
    user: dict[str, str] = Depends(get_current_user),
) -> list[ExecutionView]:
    ensure_role(user, {"admin", "operator", "viewer"})
    records = use_case.list_recent(limit=100)
    return [
        ExecutionView(
            id=r.id,
            project_id=r.project_id,
            objective=r.objective,
            agent=r.agent,
            status=r.status,
            summary=r.summary,
            error=r.error,
            duration_ms=r.duration_ms,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/{execution_id}/timeline", response_model=list[AuditEventView])
def get_timeline(
    execution_id: str,
    use_case: ListExecutionsUseCase = Depends(get_list_execution_use_case),
    user: dict[str, str] = Depends(get_current_user),
) -> list[AuditEventView]:
    ensure_role(user, {"admin", "operator", "viewer"})
    events = use_case.timeline(execution_id)
    return [
        AuditEventView(
            id=e.id,
            execution_id=e.execution_id,
            event_type=e.event_type,
            message=e.message,
            created_at=e.created_at,
        )
        for e in events
    ]
