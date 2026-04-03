from collections.abc import Sequence
from datetime import datetime

from optimus_backend.domain.entities import ApiKeyRecord

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


class PostgresApiKeyRepository:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def create(self, record: ApiKeyRecord) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_keys(id, project_id, workspace_id, name, key_prefix, key_hash, status, scopes, created_at, last_used_at, revoked_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    record.id,
                    record.project_id,
                    record.workspace_id,
                    record.name,
                    record.key_prefix,
                    record.key_hash,
                    record.status,
                    list(record.scopes),
                    record.created_at,
                    record.last_used_at,
                    record.revoked_at,
                ),
            )
            conn.commit()

    def find_active_by_prefix(self, key_prefix: str) -> ApiKeyRecord | None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, workspace_id, name, key_prefix, key_hash, status, scopes, created_at, last_used_at, revoked_at
                FROM api_keys
                WHERE key_prefix=%s AND status='active' AND revoked_at IS NULL
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (key_prefix,),
            )
            row = cur.fetchone()
        return ApiKeyRecord(*row) if row else None

    def list_by_project(self, project_id: str) -> Sequence[ApiKeyRecord]:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, workspace_id, name, key_prefix, key_hash, status, scopes, created_at, last_used_at, revoked_at
                FROM api_keys
                WHERE project_id=%s
                ORDER BY created_at DESC
                """,
                (project_id,),
            )
            rows = cur.fetchall()
        return [ApiKeyRecord(*row) for row in rows]

    def get(self, key_id: str) -> ApiKeyRecord | None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, workspace_id, name, key_prefix, key_hash, status, scopes, created_at, last_used_at, revoked_at
                FROM api_keys WHERE id=%s
                """,
                (key_id,),
            )
            row = cur.fetchone()
        return ApiKeyRecord(*row) if row else None

    def revoke(self, key_id: str, revoked_at: datetime) -> ApiKeyRecord | None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE api_keys
                SET status='revoked', revoked_at=%s
                WHERE id=%s
                RETURNING id, project_id, workspace_id, name, key_prefix, key_hash, status, scopes, created_at, last_used_at, revoked_at
                """,
                (revoked_at, key_id),
            )
            row = cur.fetchone()
            conn.commit()
        return ApiKeyRecord(*row) if row else None

    def touch_last_used(self, key_id: str, used_at: datetime) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute("UPDATE api_keys SET last_used_at=%s WHERE id=%s", (used_at, key_id))
            conn.commit()
