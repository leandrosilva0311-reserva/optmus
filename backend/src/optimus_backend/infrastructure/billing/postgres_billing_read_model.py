from optimus_backend.domain.entities import PlanDefinitionRecord, SubscriptionRecord

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


class PostgresBillingReadModel:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def list_active_plans(self) -> list[PlanDefinitionRecord]:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT plan_id, name, daily_scenario_limit, monthly_price_cents, usage_unit_price_cents, active FROM plan_definitions WHERE active=TRUE ORDER BY monthly_price_cents ASC"
            )
            rows = cur.fetchall()
        return [PlanDefinitionRecord(*row) for row in rows]

    def get_active_subscription(self, project_id: str) -> SubscriptionRecord | None:
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, plan_id, status, started_at, renews_at, cancelled_at
                FROM subscriptions
                WHERE project_id=%s AND status='active'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (project_id,),
            )
            row = cur.fetchone()
        return SubscriptionRecord(*row) if row else None
