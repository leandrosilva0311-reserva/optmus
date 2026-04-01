from datetime import UTC, datetime
from uuid import uuid4

from optimus_backend.core.specialists.agents import BaseSpecialist, SpecialistResult
from optimus_backend.domain.entities import SubtaskRecord


class Orchestrator:
    def __init__(self, specialists: dict[str, BaseSpecialist]) -> None:
        self._specialists = specialists

    def run(self, agent: str, objective: str) -> SpecialistResult:
        specialist = self._specialists.get(agent)
        if specialist is None:
            raise KeyError(f"agent '{agent}' not configured")
        return specialist.run(objective)

    def plan_subtasks(self, execution_id: str, objective: str) -> list[SubtaskRecord]:
        now = datetime.now(UTC)
        plan = [
            ("dev_architect", "Analyze architecture", []),
            ("bug_hunter", "Identify likely failure points", ["dev_architect"]),
            ("qa", "Propose validation checklist", ["bug_hunter"]),
            ("ops_sentinel", "Assess runtime/ops risks", ["dev_architect"]),
            ("analyst", f"Summarize outcome for objective: {objective}", ["qa", "ops_sentinel"]),
        ]
        return [
            SubtaskRecord(
                id=str(uuid4()),
                execution_id=execution_id,
                agent=agent,
                title=title,
                depends_on=depends,
                status="pending",
                result_summary=None,
                created_at=now,
                updated_at=now,
            )
            for agent, title, depends in plan
        ]
