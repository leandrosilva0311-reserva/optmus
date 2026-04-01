from collections.abc import Sequence

from optimus_backend.domain.entities import AuditEventRecord, ExecutionRecord
from optimus_backend.domain.ports import AuditRepository, ExecutionRepository


class ListExecutionsUseCase:
    def __init__(self, executions: ExecutionRepository, audit: AuditRepository) -> None:
        self._executions = executions
        self._audit = audit

    def list_recent(self, limit: int = 50) -> Sequence[ExecutionRecord]:
        return self._executions.list_recent(limit)

    def timeline(self, execution_id: str) -> Sequence[AuditEventRecord]:
        return self._audit.list_by_execution(execution_id)
