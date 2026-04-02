import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from dataclasses import dataclass

from fastapi.testclient import TestClient

from optimus_backend.api import dependencies
from optimus_backend.main import app
from optimus_backend.settings.config import config


@dataclass
class _StartStub:
    def execute(self, project_id: str, objective: str, agent: str):
        _ = (project_id, objective, agent)

        @dataclass
        class _Record:
            id: str = "exec-1"
            status: str = "queued"

        return _Record()


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    prev_env = config.app_env
    config.app_env = "test"
    dependencies.get_api_key_repository.cache_clear()
    dependencies.get_api_key_use_case.cache_clear()
    dependencies.get_repositories.cache_clear()
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    dependencies.get_api_key_repository.cache_clear()
    dependencies.get_api_key_use_case.cache_clear()
    dependencies.get_repositories.cache_clear()
    config.app_env = prev_env


def test_execution_run_requires_scenarios_scope_for_api_key() -> None:
    use_case = dependencies.get_api_key_use_case()
    created = use_case.create_key("project-x", "sdk", ["admin:read"])
    app.dependency_overrides[dependencies.get_start_execution_use_case] = lambda: _StartStub()

    with TestClient(app) as client:
        response = client.post(
            "/executions/run",
            json={"project_id": "project-x", "objective": "test", "agent": "qa"},
            headers={"X-API-Key": created.plaintext_key},
        )

    assert response.status_code == 403


def test_execution_run_accepts_scenarios_scope_for_api_key() -> None:
    use_case = dependencies.get_api_key_use_case()
    created = use_case.create_key("project-x", "sdk", ["scenarios:run"])
    app.dependency_overrides[dependencies.get_start_execution_use_case] = lambda: _StartStub()

    with TestClient(app) as client:
        response = client.post(
            "/executions/run",
            json={"project_id": "project-x", "objective": "test", "agent": "qa"},
            headers={"X-API-Key": created.plaintext_key},
        )

    assert response.status_code == 200
    assert response.json()["execution_id"] == "exec-1"
