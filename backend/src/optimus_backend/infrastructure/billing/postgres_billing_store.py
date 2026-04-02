from datetime import UTC, datetime, timedelta
from uuid import uuid4

from optimus_backend.domain.entities import (
    BillingCycleClosureRecord,
    InvoiceRecord,
    InvoiceStatusTransitionRecord,
    InvoiceItemRecord,
    PlanDefinitionRecord,
    SubscriptionPlanChangeRecord,
    SubscriptionRecord,
    UsageHistoryRecord,
)

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


class PostgresBillingStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _conn(self):
        if psycopg is None:
            raise RuntimeError("psycopg not installed")
        return psycopg.connect(self._dsn)

    def _is_unique_violation(self, exc: Exception) -> bool:
        if psycopg is None:
            return False
        errors = getattr(psycopg, "errors", None)
        unique_violation = getattr(errors, "UniqueViolation", None) if errors else None
        return bool(unique_violation and isinstance(exc, unique_violation))

    def list_active_plans(self) -> list[PlanDefinitionRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT plan_id, name, daily_scenario_limit, monthly_price_cents, usage_unit_price_cents, active FROM plan_definitions WHERE active=TRUE"
            )
            rows = cur.fetchall()
        return [PlanDefinitionRecord(*row) for row in rows]

    def get_plan(self, plan_id: str) -> PlanDefinitionRecord | None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT plan_id, name, daily_scenario_limit, monthly_price_cents, usage_unit_price_cents, active FROM plan_definitions WHERE plan_id=%s",
                (plan_id,),
            )
            row = cur.fetchone()
        return PlanDefinitionRecord(*row) if row else None

    def get_active_subscription(self, project_id: str) -> SubscriptionRecord | None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, project_id, plan_id, status, started_at, renews_at, cancelled_at FROM subscriptions WHERE project_id=%s AND status IN ('active','cancelling') ORDER BY created_at DESC LIMIT 1",
                (project_id,),
            )
            row = cur.fetchone()
        return SubscriptionRecord(*row) if row else None

    def list_invoices(self, project_id: str) -> list[InvoiceRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, project_id, period_start, period_end, status, total_cents, created_at FROM invoices WHERE project_id=%s ORDER BY created_at DESC",
                (project_id,),
            )
            rows = cur.fetchall()
        return [InvoiceRecord(*row) for row in rows]

    def list_invoice_items(self, invoice_id: str) -> list[InvoiceItemRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, invoice_id, item_type, quantity, unit_price_cents, total_cents, description
                FROM invoice_items
                WHERE invoice_id=%s
                ORDER BY id
                """,
                (invoice_id,),
            )
            rows = cur.fetchall()
        return [InvoiceItemRecord(*row) for row in rows]

    def list_invoice_status_transitions(self, invoice_id: str) -> list[InvoiceStatusTransitionRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, invoice_id, from_status, to_status, changed_by, changed_at
                FROM invoice_status_transitions
                WHERE invoice_id=%s
                ORDER BY changed_at DESC
                """,
                (invoice_id,),
            )
            rows = cur.fetchall()
        return [InvoiceStatusTransitionRecord(*row) for row in rows]

    def usage_history(self, project_id: str, date_from: datetime, date_to: datetime) -> list[UsageHistoryRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT event_date, SUM(units) FROM usage_events WHERE project_id=%s AND event_date BETWEEN %s AND %s GROUP BY event_date ORDER BY event_date DESC",
                (project_id, date_from.date(), date_to.date()),
            )
            rows = cur.fetchall()
        return [UsageHistoryRecord(event_date=datetime.combine(r[0], datetime.min.time(), tzinfo=UTC), units=int(r[1])) for r in rows]

    def list_plan_changes(self, project_id: str) -> list[SubscriptionPlanChangeRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, from_plan_id, to_plan_id, effective_at, status, created_at
                FROM subscription_plan_changes
                WHERE project_id=%s
                ORDER BY created_at DESC
                """,
                (project_id,),
            )
            rows = cur.fetchall()
        return [SubscriptionPlanChangeRecord(*row) for row in rows]

    def list_cycle_closures(self, project_id: str) -> list[BillingCycleClosureRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, period_start, period_end, invoice_id, usage_units, closed_by, created_at
                FROM billing_cycle_closures
                WHERE project_id=%s
                ORDER BY created_at DESC
                """,
                (project_id,),
            )
            rows = cur.fetchall()
        return [BillingCycleClosureRecord(*row) for row in rows]

    def list_active_subscriptions_due(self, as_of: datetime) -> list[SubscriptionRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, plan_id, status, started_at, renews_at, cancelled_at
                FROM subscriptions
                WHERE status IN ('active', 'cancelling') AND renews_at IS NOT NULL AND renews_at <= %s
                ORDER BY renews_at ASC
                """,
                (as_of,),
            )
            rows = cur.fetchall()
        return [SubscriptionRecord(*row) for row in rows]

    def create_subscription(self, project_id: str, plan_id: str, actor_id: str = "system") -> SubscriptionRecord:
        _ = actor_id
        now = datetime.now(UTC)
        sub = SubscriptionRecord(str(uuid4()), project_id, plan_id, "pending_activation", now, None, None)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("UPDATE subscriptions SET status='cancelled' WHERE project_id=%s AND status IN ('active','cancelling','pending_activation')", (project_id,))
            cur.execute(
                "INSERT INTO subscriptions(id, project_id, plan_id, status, started_at, renews_at, cancelled_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (sub.id, sub.project_id, sub.plan_id, sub.status, sub.started_at, sub.renews_at, sub.cancelled_at),
            )
            conn.commit()
        return sub

    def activate_subscription(self, project_id: str, actor_id: str = "system") -> SubscriptionRecord:
        _ = actor_id
        now = datetime.now(UTC)
        renews_at = now + timedelta(days=30)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE subscriptions
                SET status='active', started_at=%s, renews_at=%s
                WHERE id = (
                  SELECT id FROM subscriptions
                  WHERE project_id=%s AND status IN ('pending_activation', 'active', 'cancelling')
                  ORDER BY created_at DESC
                  LIMIT 1
                )
                RETURNING id, project_id, plan_id, status, started_at, renews_at, cancelled_at
                """,
                (now, renews_at, project_id),
            )
            row = cur.fetchone()
            conn.commit()
        if row is None:
            raise KeyError("subscription not found")
        return SubscriptionRecord(*row)

    def create_or_activate_subscription(self, project_id: str, plan_id: str, actor_id: str = "system") -> SubscriptionRecord:
        self.create_subscription(project_id, plan_id, actor_id=actor_id)
        return self.activate_subscription(project_id, actor_id=actor_id)

    def change_plan(self, project_id: str, new_plan_id: str) -> SubscriptionPlanChangeRecord:
        sub = self.get_active_subscription(project_id)
        if sub is None:
            raise KeyError("active subscription not found")
        old_plan = self.get_plan(sub.plan_id)
        new_plan = self.get_plan(new_plan_id)
        if old_plan is None or new_plan is None:
            raise KeyError("plan not found")

        now = datetime.now(UTC)
        status = "applied" if new_plan.monthly_price_cents > old_plan.monthly_price_cents else "scheduled"
        effective_at = now if status == "applied" else (sub.renews_at or (now + timedelta(days=30)))

        change = SubscriptionPlanChangeRecord(str(uuid4()), project_id, sub.plan_id, new_plan_id, effective_at, status, now)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO subscription_plan_changes(id, project_id, from_plan_id, to_plan_id, effective_at, status, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (change.id, change.project_id, change.from_plan_id, change.to_plan_id, change.effective_at, change.status, change.created_at),
            )
            if status == "applied":
                cur.execute("UPDATE subscriptions SET plan_id=%s WHERE id=%s", (new_plan_id, sub.id))
            conn.commit()
        return change

    def cancel_subscription(self, project_id: str) -> SubscriptionRecord:
        sub = self.get_active_subscription(project_id)
        if sub is None:
            raise KeyError("active subscription not found")
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("UPDATE subscriptions SET status='cancelling', cancelled_at=renews_at WHERE id=%s", (sub.id,))
            conn.commit()
        return SubscriptionRecord(sub.id, sub.project_id, sub.plan_id, "cancelling", sub.started_at, sub.renews_at, sub.renews_at)

    def close_billing_cycle(self, project_id: str, period_start: datetime, period_end: datetime, actor_id: str = "system") -> InvoiceRecord:
        if period_start >= period_end:
            raise ValueError("period_start must be before period_end")
        sub = self.get_active_subscription(project_id)
        if sub is None:
            raise KeyError("active subscription not found")
        plan = self.get_plan(sub.plan_id)
        if plan is None:
            raise KeyError("plan not found")

        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, period_start, period_end, status, total_cents, created_at
                FROM invoices
                WHERE project_id=%s AND period_start=%s AND period_end=%s
                LIMIT 1
                """,
                (project_id, period_start.date(), period_end.date()),
            )
            existing = cur.fetchone()
        if existing:
            return InvoiceRecord(*existing)

        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(SUM(units), 0)
                FROM usage_events
                WHERE project_id=%s AND event_date BETWEEN %s AND %s
                """,
                (project_id, period_start.date(), period_end.date()),
            )
            usage_units = int(cur.fetchone()[0])

        usage_unit_price_cents = plan.usage_unit_price_cents
        usage_total_cents = usage_units * usage_unit_price_cents
        invoice = InvoiceRecord(
            str(uuid4()),
            project_id,
            period_start,
            period_end,
            "open",
            plan.monthly_price_cents + usage_total_cents,
            datetime.now(UTC),
        )
        try:
            with self._conn() as conn, conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO invoices(id, project_id, period_start, period_end, status, total_cents, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (invoice.id, invoice.project_id, invoice.period_start.date(), invoice.period_end.date(), invoice.status, invoice.total_cents, invoice.created_at),
                )
                cur.execute(
                    """
                    INSERT INTO invoice_status_transitions(id, invoice_id, from_status, to_status, changed_by, changed_at)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """,
                    (str(uuid4()), invoice.id, "none", "open", actor_id, datetime.now(UTC)),
                )
                cur.execute(
                    "INSERT INTO invoice_items(id, invoice_id, item_type, quantity, unit_price_cents, total_cents, description) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (str(uuid4()), invoice.id, "subscription_fee", 1, plan.monthly_price_cents, plan.monthly_price_cents, f"Plano {plan.name}"),
                )
                if usage_units > 0:
                    cur.execute(
                        "INSERT INTO invoice_items(id, invoice_id, item_type, quantity, unit_price_cents, total_cents, description) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (str(uuid4()), invoice.id, "usage_fee", usage_units, usage_unit_price_cents, usage_total_cents, "Consumo de cenários no período"),
                    )
                cur.execute(
                    "UPDATE subscription_plan_changes SET status='applied' WHERE project_id=%s AND status='scheduled' AND effective_at<=%s",
                    (project_id, period_end),
                )
                cur.execute(
                    """
                    UPDATE subscriptions
                    SET plan_id=sub_changes.to_plan_id
                    FROM (
                      SELECT to_plan_id
                      FROM subscription_plan_changes
                      WHERE project_id=%s AND status='applied'
                      ORDER BY effective_at DESC
                      LIMIT 1
                    ) AS sub_changes
                    WHERE subscriptions.project_id=%s AND subscriptions.status IN ('active', 'cancelling')
                    """,
                    (project_id, project_id),
                )
                cur.execute(
                    """
                    INSERT INTO billing_cycle_closures(id, project_id, period_start, period_end, invoice_id, usage_units, closed_by, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (project_id, period_start, period_end) DO NOTHING
                    """,
                    (str(uuid4()), project_id, period_start.date(), period_end.date(), invoice.id, usage_units, actor_id, datetime.now(UTC)),
                )
                conn.commit()
        except Exception as exc:
            if not self._is_unique_violation(exc):
                raise
            with self._conn() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, project_id, period_start, period_end, status, total_cents, created_at
                    FROM invoices
                    WHERE project_id=%s AND period_start=%s AND period_end=%s
                    LIMIT 1
                    """,
                    (project_id, period_start.date(), period_end.date()),
                )
                existing = cur.fetchone()
            if existing:
                return InvoiceRecord(*existing)
            raise
        return invoice

    def update_invoice_status(self, invoice_id: str, to_status: str, actor_id: str = "system") -> InvoiceRecord:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, period_start, period_end, status, total_cents, created_at
                FROM invoices
                WHERE id=%s
                LIMIT 1
                """,
                (invoice_id,),
            )
            current = cur.fetchone()
            if not current:
                raise KeyError("invoice not found")
            current_invoice = InvoiceRecord(*current)
            cur.execute("UPDATE invoices SET status=%s WHERE id=%s", (to_status, invoice_id))
            cur.execute(
                """
                INSERT INTO invoice_status_transitions(id, invoice_id, from_status, to_status, changed_by, changed_at)
                VALUES (%s,%s,%s,%s,%s,%s)
                """,
                (str(uuid4()), invoice_id, current_invoice.status, to_status, actor_id, datetime.now(UTC)),
            )
            conn.commit()
        return InvoiceRecord(
            current_invoice.id,
            current_invoice.project_id,
            current_invoice.period_start,
            current_invoice.period_end,
            to_status,
            current_invoice.total_cents,
            current_invoice.created_at,
        )
