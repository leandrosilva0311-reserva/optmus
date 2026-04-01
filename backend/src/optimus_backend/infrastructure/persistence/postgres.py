from collections.abc import Sequence
from datetime import UTC, datetime

from optimus_backend.domain.entities import AuditEventRecord, ExecutionRecord

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


def now_utc() -> datetime:
    return datetime.now(UTC)
