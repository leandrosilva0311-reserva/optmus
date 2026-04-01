from collections.abc import Sequence

from optimus_backend.domain.entities import AuditEventRecord, ExecutionRecord, UserRecord


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


class InMemoryAuditRepository:
    def __init__(self) -> None:
        self._items: list[AuditEventRecord] = []

    def append(self, event: AuditEventRecord) -> None:
        self._items.append(event)

    def list_by_execution(self, execution_id: str) -> Sequence[AuditEventRecord]:
        return [i for i in self._items if i.execution_id == execution_id]


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
        self._users = {u.email: u for u in users}

    def find_by_email(self, email: str) -> UserRecord | None:
        return self._users.get(email)


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
