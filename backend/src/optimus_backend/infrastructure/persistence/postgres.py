from collections.abc import Sequence

from optimus_backend.domain.entities import (
    AuditEventRecord,
    ExecutionRecord,
    MemoryEntry,
    SubtaskRecord,
    UserRecord,
)

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


class PostgresExecutionRepository:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def create(self, record: ExecutionRecord) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO executions(id, project_id, objective, agent, status, summary, error, duration_ms, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    record.id,
                    record.project_id,
                    record.objective,
                    record.agent,
                    record.status,
                    record.summary,
                    record.error,
                    record.duration_ms,
                    record.created_at,
                    record.updated_at,
                ),
            )
            conn.commit()

    def update(self, record: ExecutionRecord) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE executions
                SET status=%s, summary=%s, error=%s, duration_ms=%s, updated_at=%s
                WHERE id=%s
                """,
                (record.status, record.summary, record.error, record.duration_ms, record.updated_at, record.id),
            )
            conn.commit()

    def get(self, execution_id: str) -> ExecutionRecord | None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, objective, agent, status, summary, error, duration_ms, created_at, updated_at
                FROM executions WHERE id=%s
                """,
                (execution_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return ExecutionRecord(*row)

    def list_recent(self, limit: int = 50) -> Sequence[ExecutionRecord]:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, objective, agent, status, summary, error, duration_ms, created_at, updated_at
                FROM executions ORDER BY created_at DESC LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
        return [ExecutionRecord(*row) for row in rows]


class PostgresSubtaskRepository:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def create_many(self, subtasks: list[SubtaskRecord]) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            for s in subtasks:
                cur.execute(
                    """
                    INSERT INTO subtasks(id, execution_id, agent, title, depends_on, status, result_summary, created_at, updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (s.id, s.execution_id, s.agent, s.title, s.depends_on, s.status, s.result_summary, s.created_at, s.updated_at),
                )
            conn.commit()

    def update(self, subtask: SubtaskRecord) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE subtasks SET status=%s, result_summary=%s, updated_at=%s WHERE id=%s
                """,
                (subtask.status, subtask.result_summary, subtask.updated_at, subtask.id),
            )
            conn.commit()

    def list_by_execution(self, execution_id: str) -> Sequence[SubtaskRecord]:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, execution_id, agent, title, depends_on, status, result_summary, created_at, updated_at FROM subtasks WHERE execution_id=%s ORDER BY created_at ASC",
                (execution_id,),
            )
            rows = cur.fetchall()
        return [SubtaskRecord(*row) for row in rows]


class PostgresAuditRepository:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def append(self, event: AuditEventRecord) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO audit_events(id, execution_id, event_type, message, created_at) VALUES (%s,%s,%s,%s,%s)",
                (event.id, event.execution_id, event.event_type, event.message, event.created_at),
            )
            conn.commit()

    def list_by_execution(self, execution_id: str) -> Sequence[AuditEventRecord]:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, execution_id, event_type, message, created_at FROM audit_events WHERE execution_id=%s ORDER BY created_at ASC",
                (execution_id,),
            )
            rows = cur.fetchall()
        return [AuditEventRecord(*row) for row in rows]


class PostgresMemoryRepository:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def add(self, entry: MemoryEntry) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO memory_entries(id, project_id, entry_type, source, confidence, content, status, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    entry.id,
                    entry.project_id,
                    entry.entry_type,
                    entry.source,
                    entry.confidence,
                    entry.content,
                    entry.status,
                    entry.created_at,
                ),
            )
            conn.commit()

    def list_for_project(self, project_id: str, status: str | None = None) -> Sequence[MemoryEntry]:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        query = "SELECT id, project_id, entry_type, source, confidence, content, status, created_at FROM memory_entries WHERE project_id=%s"
        params: tuple[object, ...] = (project_id,)
        if status:
            query += " AND status=%s"
            params = (project_id, status)
        query += " ORDER BY created_at DESC"
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        return [MemoryEntry(*row) for row in rows]

    def approve(self, entry_id: str) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute("UPDATE memory_entries SET status='approved' WHERE id=%s", (entry_id,))
            conn.commit()


class PostgresUserRepository:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def find_by_email(self, email: str) -> UserRecord | None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute("SELECT id, email, password_hash, role FROM users WHERE email=%s", (email,))
            row = cur.fetchone()
        return UserRecord(*row) if row else None

    def find_by_id(self, user_id: str) -> UserRecord | None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute("SELECT id, email, password_hash, role FROM users WHERE id=%s", (user_id,))
            row = cur.fetchone()
        return UserRecord(*row) if row else None
