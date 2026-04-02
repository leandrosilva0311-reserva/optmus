from datetime import UTC, datetime

from optimus_backend.core.usage.metering import limit_for_plan


class InMemoryUsageMeter:
    def __init__(self) -> None:
        self._consumed: dict[str, int] = {}

    def _key(self, project_id: str, plan_id: str) -> str:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        return f"{project_id}:{plan_id}:{today}"

    def consume(self, project_id: str, plan_id: str, units: int = 1) -> tuple[bool, int, int]:
        key = self._key(project_id, plan_id)
        current = self._consumed.get(key, 0)
        limit = limit_for_plan(plan_id)
        new_total = current + units
        if new_total > limit:
            return False, current, limit
        self._consumed[key] = new_total
        return True, new_total, limit

    def current(self, project_id: str, plan_id: str) -> tuple[int, int]:
        key = self._key(project_id, plan_id)
        return self._consumed.get(key, 0), limit_for_plan(plan_id)
