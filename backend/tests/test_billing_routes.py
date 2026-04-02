import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from optimus_backend.api import dependencies
from optimus_backend.infrastructure.billing.in_memory_billing_store import InMemoryBillingStore
from optimus_backend.infrastructure.billing.in_memory_usage_meter import InMemoryUsageMeter
from optimus_backend.main import app


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
