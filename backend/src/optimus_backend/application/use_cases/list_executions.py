from collections.abc import Sequence

from optimus_backend.domain.entities import AuditEventRecord, ExecutionRecord, SubtaskRecord
from optimus_backend.domain.ports import AuditRepository, ExecutionRepository, SubtaskRepository


class ListExecutionsUseCase:
    def __init__(self, executions: ExecutionRepository, subtasks: SubtaskRepository, audit: AuditRepository) -> None:
        self._executions = executions
        self._subtasks = subtasks
        self._audit = audit

    def list_recent(self, limit: int = 50) -> Sequence[ExecutionRecord]:
        return self._executions.list_recent(limit)

    def timeline(self, execution_id: str) -> Sequence[AuditEventRecord]:
        return self._audit.list_by_execution(execution_id)

    def subtasks(self, execution_id: str) -> Sequence[SubtaskRecord]:
        return self._subtasks.list_by_execution(execution_id)
