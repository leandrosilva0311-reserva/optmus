from collections.abc import Sequence

from optimus_backend.domain.entities import AuditEventRecord, ExecutionRecord, MemoryEntry, SubtaskRecord, UserRecord


class InMemoryExecutionRepository:
    def __init__(self) -> None:
        self._items: dict[str, ExecutionRecord] = {}

    def create(self, record: ExecutionRecord) -> None:
        self._items[record.id] = record

    def update(self, record: ExecutionRecord) -> None:
        self._items[record.id] = record

    def get(self, execution_id: str) -> ExecutionRecord | None:
        return self._items.get(execution_id)

    def list_recent(self, limit: int = 50) -> Sequence[ExecutionRecord]:
        return list(self._items.values())[-limit:][::-1]


class InMemorySubtaskRepository:
    def __init__(self) -> None:
        self._items: dict[str, SubtaskRecord] = {}

    def create_many(self, subtasks: list[SubtaskRecord]) -> None:
        for subtask in subtasks:
            self._items[subtask.id] = subtask

    def update(self, subtask: SubtaskRecord) -> None:
        self._items[subtask.id] = subtask

    def list_by_execution(self, execution_id: str) -> Sequence[SubtaskRecord]:
        return [s for s in self._items.values() if s.execution_id == execution_id]


class InMemoryAuditRepository:
    def __init__(self) -> None:
        self._items: list[AuditEventRecord] = []

    def append(self, event: AuditEventRecord) -> None:
        self._items.append(event)

    def list_by_execution(self, execution_id: str) -> Sequence[AuditEventRecord]:
        return [i for i in self._items if i.execution_id == execution_id]


class InMemoryMemoryRepository:
    def __init__(self) -> None:
        self._items: dict[str, MemoryEntry] = {}

    def add(self, entry: MemoryEntry) -> None:
        self._items[entry.id] = entry

    def list_for_project(self, project_id: str, status: str | None = None) -> Sequence[MemoryEntry]:
        items = [e for e in self._items.values() if e.project_id == project_id]
        if status:
            return [e for e in items if e.status == status]
        return items

    def approve(self, entry_id: str) -> None:
        item = self._items.get(entry_id)
        if item:
            item.status = "approved"


class InMemorySessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, str] = {}

    def save(self, session_id: str, user_id: str, ttl_seconds: int) -> None:
        _ = ttl_seconds
        self._sessions[session_id] = user_id

    def get_user_id(self, session_id: str) -> str | None:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


class InMemoryUserRepository:
    def __init__(self, users: list[UserRecord]) -> None:
        self._users_by_email = {u.email: u for u in users}
        self._users_by_id = {u.id: u for u in users}

    def find_by_email(self, email: str) -> UserRecord | None:
        return self._users_by_email.get(email)

    def find_by_id(self, user_id: str) -> UserRecord | None:
        return self._users_by_id.get(user_id)


class InMemoryLockManager:
    def __init__(self) -> None:
        self._locks: set[str] = set()

    def acquire(self, key: str, ttl_seconds: int) -> bool:
        _ = ttl_seconds
        if key in self._locks:
            return False
        self._locks.add(key)
        return True

    def release(self, key: str) -> None:
        self._locks.discard(key)
