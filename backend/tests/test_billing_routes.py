import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from optimus_backend.application.jobs.billing_cycle_closer import BillingCycleRunReport
from optimus_backend.api import dependencies
from optimus_backend.domain.entities import InvoiceRecord
from optimus_backend.infrastructure.billing.in_memory_billing_store import InMemoryBillingStore
from optimus_backend.infrastructure.billing.in_memory_usage_meter import InMemoryUsageMeter
from optimus_backend.main import app
from optimus_backend.settings.config import config


@pytest.fixture(autouse=True)
def _reset_dependency_state() -> None:
    previous_env = config.app_env
    config.app_env = "test"
    dependencies.get_billing_store.cache_clear()
    dependencies.get_billing_read_model.cache_clear()
    dependencies.get_billing_command_model.cache_clear()
    dependencies.get_billing_cycle_closer.cache_clear()
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    dependencies.get_billing_store.cache_clear()
    dependencies.get_billing_read_model.cache_clear()
    dependencies.get_billing_command_model.cache_clear()
    dependencies.get_billing_cycle_closer.cache_clear()
    config.app_env = previous_env


def _override_admin_user() -> dict[str, str]:
    return {"user_id": "u-admin", "role": "admin", "session_id": "s-1", "checked_at": "2026-01-01T00:00:00Z"}


def _override_viewer_user() -> dict[str, str]:
    return {"user_id": "u-viewer", "role": "viewer", "session_id": "s-2", "checked_at": "2026-01-01T00:00:00Z"}


def test_billing_role_error_is_standardized() -> None:
    store = InMemoryBillingStore()
    app.dependency_overrides[dependencies.get_current_user] = _override_viewer_user
    app.dependency_overrides[dependencies.get_billing_read_model] = lambda: store
    app.dependency_overrides[dependencies.get_billing_command_model] = lambda: store
    app.dependency_overrides[dependencies.get_usage_meter] = InMemoryUsageMeter

    with TestClient(app) as client:
        response = client.post("/billing/subscription", json={"project_id": "p-1", "plan_id": "starter"})
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "billing_forbidden"


def test_billing_not_found_error_is_standardized() -> None:
    store = InMemoryBillingStore()
    app.dependency_overrides[dependencies.get_current_user] = _override_admin_user
    app.dependency_overrides[dependencies.get_billing_read_model] = lambda: store
    app.dependency_overrides[dependencies.get_billing_command_model] = lambda: store
    app.dependency_overrides[dependencies.get_usage_meter] = InMemoryUsageMeter

    with TestClient(app) as client:
        response = client.get("/billing/subscription", params={"project_id": "missing-project"})
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "billing_not_found"


def test_subscription_create_and_activate_routes() -> None:
    store = InMemoryBillingStore()
    app.dependency_overrides[dependencies.get_current_user] = _override_admin_user
    app.dependency_overrides[dependencies.get_billing_read_model] = lambda: store
    app.dependency_overrides[dependencies.get_billing_command_model] = lambda: store
    app.dependency_overrides[dependencies.get_usage_meter] = InMemoryUsageMeter

    with TestClient(app) as client:
        created = client.post("/billing/subscription/create", json={"project_id": "p-admin", "plan_id": "starter"})
        activated = client.post("/billing/subscription/activate", json={"project_id": "p-admin"})
    app.dependency_overrides.clear()

    assert created.status_code == 200
    assert created.json()["status"] == "pending_activation"
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"


def test_run_due_cycle_route_returns_report() -> None:
    app.dependency_overrides[dependencies.get_current_user] = _override_admin_user
    app.dependency_overrides[dependencies.get_billing_cycle_closer] = lambda: type(
        "CloserStub",
        (),
        {
            "run_due_cycles": lambda self, as_of, actor_id="billing-job": BillingCycleRunReport(
                started_at=as_of,
                finished_at=as_of,
                processed_subscriptions=2,
                generated_invoices=1,
                failed_subscriptions=1,
                duration_ms=123,
                invoices=[InvoiceRecord("i-1", "p-1", as_of, as_of, "open", 1000, as_of)],
                failures=["p-fail"],
            )
        },
    )()

    with TestClient(app) as client:
        response = client.post("/billing/cycle/run-due", json={"as_of": datetime.now(UTC).isoformat()})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["processed_subscriptions"] == 2
    assert response.json()["generated_invoices"] == 1


def test_run_due_cycle_route_conflict() -> None:
    app.dependency_overrides[dependencies.get_current_user] = _override_admin_user
    app.dependency_overrides[dependencies.get_billing_cycle_closer] = lambda: type(
        "CloserConflictStub",
        (),
        {"run_due_cycles": lambda self, as_of, actor_id="billing-job": (_ for _ in ()).throw(RuntimeError("already in progress"))},
    )()

    with TestClient(app) as client:
        response = client.post("/billing/cycle/run-due", json={"as_of": datetime.now(UTC).isoformat()})
    app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "billing_job_conflict"


def test_invoice_status_change_route() -> None:
    store = InMemoryBillingStore()
    sub = store.create_or_activate_subscription("p-inv", "starter")
    assert sub.status == "active"
    invoice = store.close_billing_cycle("p-inv", datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 31, tzinfo=UTC))
    app.dependency_overrides[dependencies.get_current_user] = _override_admin_user
    app.dependency_overrides[dependencies.get_billing_command_model] = lambda: store

    with TestClient(app) as client:
        response = client.post("/billing/invoices/status", json={"invoice_id": invoice.id, "to_status": "issued"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "issued"


def test_scheduler_config_endpoint() -> None:
    app.dependency_overrides[dependencies.get_current_user] = _override_admin_user
    with TestClient(app) as client:
        response = client.get("/billing/cycle/scheduler/config")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["cron_expression"] == "0 * * * *"
