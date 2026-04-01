from datetime import UTC, datetime

from optimus_backend.core.usage.metering import limit_for_plan

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


class PostgresUsageMeter:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _today(self):
        return datetime.now(UTC).date()

    def consume(self, project_id: str, plan_id: str, units: int = 1) -> tuple[bool, int, int]:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")

        today = self._today()
        limit = limit_for_plan(plan_id)

        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO usage_daily_counters(project_id, plan_id, event_date, consumed_units)
                VALUES (%s, %s, %s, 0)
                ON CONFLICT (project_id, plan_id, event_date) DO NOTHING
                """,
                (project_id, plan_id, today),
            )

            cur.execute(
                """
                SELECT consumed_units
                FROM usage_daily_counters
                WHERE project_id=%s AND plan_id=%s AND event_date=%s
                FOR UPDATE
                """,
                (project_id, plan_id, today),
            )
            row = cur.fetchone()
            current = int(row[0]) if row else 0
            proposed = current + units

            if proposed > limit:
                conn.rollback()
                return False, current, limit

            cur.execute(
                """
                UPDATE usage_daily_counters
                SET consumed_units=%s
                WHERE project_id=%s AND plan_id=%s AND event_date=%s
                """,
                (proposed, project_id, plan_id, today),
            )
            cur.execute(
                """
                INSERT INTO usage_events(project_id, plan_id, scenario_id, units, event_date, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (project_id, plan_id, "scenario_run", units, today, datetime.now(UTC)),
            )
            conn.commit()

        return True, proposed, limit

    def current(self, project_id: str, plan_id: str) -> tuple[int, int]:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")

        today = self._today()
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT consumed_units FROM usage_daily_counters WHERE project_id=%s AND plan_id=%s AND event_date=%s",
                (project_id, plan_id, today),
            )
            row = cur.fetchone()
        consumed = int(row[0]) if row else 0
        return consumed, limit_for_plan(plan_id)
