import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from optimus_backend.api import dependencies
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


def _code_analysis_payload(project_id: str) -> dict:
    return {
        "project_id": project_id,
        "scenario_id": "code_analysis",
        "objective": "Diagnosticar hotspots de acoplamento",
        "inputs": {
            "stack": "python-fastapi",
            "objective": "reduzir acoplamento",
            "files": [
                {
                    "path": "src/service.py",
                    "content": "def handler():\n    return 1",
                }
            ],
        },
    }


def test_scenarios_run_contract_success_and_request_id_propagation() -> None:
    created = dependencies.get_api_key_use_case().create_key("p-int", "kaiso", ["scenarios:run"])
    payload = _code_analysis_payload("p-int")

    with TestClient(app) as client:
        response = client.post(
            "/scenarios/run",
            json=payload,
            headers={"Authorization": f"Bearer {created.plaintext_key}", "X-Request-Id": "kaiso-req-123"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["execution_id"]
    assert body["status"] in {"queued", "running", "completed"}
    assert isinstance(body["reused"], bool)
    assert body["usage"]["plan_id"] == "starter"
    assert body["request_id"] == "kaiso-req-123"
    assert body["scenario_id"] == "code_analysis"
    assert body["deprecated_alias_used"] is False
    assert response.headers.get("X-Request-Id") == "kaiso-req-123"


def test_scenarios_run_contract_requires_scope() -> None:
    created = dependencies.get_api_key_use_case().create_key("p-int", "kaiso", ["admin:read"])
    payload = _code_analysis_payload("p-int")

    with TestClient(app) as client:
        response = client.post("/scenarios/run", json=payload, headers={"X-API-Key": created.plaintext_key})

    assert response.status_code == 403
