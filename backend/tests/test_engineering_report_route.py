import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from optimus_backend.api import dependencies
from optimus_backend.infrastructure.queue.worker import run_execution_job
from optimus_backend.main import app
from optimus_backend.settings.config import config


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    prev_env = config.app_env
    config.app_env = "test"
    dependencies.get_api_key_repository.cache_clear()
    dependencies.get_api_key_use_case.cache_clear()
    dependencies.get_repositories.cache_clear()
    dependencies.get_billing_store.cache_clear()
    dependencies.get_billing_read_model.cache_clear()
    dependencies.get_billing_command_model.cache_clear()
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    dependencies.get_api_key_repository.cache_clear()
    dependencies.get_api_key_use_case.cache_clear()
    dependencies.get_repositories.cache_clear()
    dependencies.get_billing_store.cache_clear()
    dependencies.get_billing_read_model.cache_clear()
    dependencies.get_billing_command_model.cache_clear()
    config.app_env = prev_env


def _payload(project_id: str) -> dict[str, object]:
    return {
        "project_id": project_id,
        "scenario_id": "patch_review",
        "objective": "validar patch",
        "inputs": {
            "diff_text": "--- a/a.py\n+++ b/a.py\n@@\n-return 1\n+return 2",
            "objective": "review",
            "stack": "python",
        },
    }


def test_engineering_report_endpoint_returns_dedicated_payload() -> None:
    created = dependencies.get_api_key_use_case().create_key("p-er", "kaiso", ["scenarios:run", "admin:read"])

    with TestClient(app) as client:
        run_response = client.post("/scenarios/run", json=_payload("p-er"), headers={"X-API-Key": created.plaintext_key})
        assert run_response.status_code == 200
        execution_id = run_response.json()["execution_id"]

    run_execution_job({}, execution_id)
    _, _, _, memory, _, _, _, _, _ = dependencies.get_repositories()
    artifacts = [
        item for item in memory.list_for_project("p-er") if item.entry_type == "engineering_report" and item.source == execution_id
    ]
    assert artifacts

    with TestClient(app) as client:
        report_response = client.get(f"/scenarios/{execution_id}/engineering-report", headers={"X-API-Key": created.plaintext_key})

    assert report_response.status_code == 200
    body = report_response.json()
    assert body["execution_id"] == execution_id
    assert body["scenario_id"] == "patch_review"
    assert body["diagnosis"]
    assert body["generated_at"]


def test_engineering_report_endpoint_returns_404_when_missing() -> None:
    created = dependencies.get_api_key_use_case().create_key("p-er", "kaiso", ["admin:read"])

    with TestClient(app) as client:
        response = client.get("/scenarios/non-existent/engineering-report", headers={"X-API-Key": created.plaintext_key})

    assert response.status_code == 404
