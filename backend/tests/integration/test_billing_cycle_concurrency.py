import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration
psycopg = pytest.importorskip("psycopg")

from optimus_backend.infrastructure.billing.postgres_billing_store import PostgresBillingStore


def _run_migrations(database_url: str) -> None:
    sql_dir = Path(__file__).resolve().parents[2] / "sql"
    migration_files = ["001_init.sql", "002_billing_init.sql", "003_billing_cycle.sql", "004_billing_operational.sql", "005_billing_usage_unit_pricing.sql"]
    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        for filename in migration_files:
            cur.execute((sql_dir / filename).read_text(encoding="utf-8"))
        conn.commit()


@pytest.mark.skipif(not os.getenv("INTEGRATION_REAL"), reason="Set INTEGRATION_REAL=1 to run with PostgreSQL")
def test_close_cycle_concurrent_postgres_is_idempotent() -> None:
    database_url = os.environ["DATABASE_URL"]
    _run_migrations(database_url)
    project_id = f"integration-billing-{uuid4()}"
    period_start = datetime(2026, 1, 1, tzinfo=UTC)
    period_end = datetime(2026, 1, 31, tzinfo=UTC)

    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO subscriptions(id, project_id, plan_id, status, started_at, renews_at, cancelled_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (str(uuid4()), project_id, "starter", "active", datetime.now(UTC), datetime(2026, 2, 1, tzinfo=UTC), None),
        )
        cur.execute(
            """
            INSERT INTO usage_events(project_id, plan_id, scenario_id, units, event_date, created_at)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (project_id, "starter", "scenario_run", 3, period_end.date(), datetime.now(UTC)),
        )
        conn.commit()

    def _close_once() -> str:
        store = PostgresBillingStore(database_url)
        invoice = store.close_billing_cycle(project_id, period_start, period_end, actor_id="integration-test")
        return invoice.id

    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = list(executor.map(lambda _: _close_once(), [1, 2]))

    assert first == second

    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM invoices WHERE project_id=%s AND period_start=%s AND period_end=%s", (project_id, period_start.date(), period_end.date()))
        invoice_count = int(cur.fetchone()[0])
        cur.execute(
            "SELECT COUNT(*) FROM billing_cycle_closures WHERE project_id=%s AND period_start=%s AND period_end=%s",
            (project_id, period_start.date(), period_end.date()),
        )
        closure_count = int(cur.fetchone()[0])
    assert invoice_count == 1
    assert closure_count == 1
