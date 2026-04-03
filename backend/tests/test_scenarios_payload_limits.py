from pathlib import Path

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


def _api_key(scopes: list[str] | None = None) -> str:
    key = dependencies.get_api_key_use_case().create_key("p-limits", "kaiso", scopes or ["scenarios:run"])
    return key.plaintext_key


def test_scenarios_run_accepts_large_diff_text_and_multiple_files() -> None:
    payload = {
        "project_id": "p-limits",
        "scenario_id": "patch_review",
        "objective": "revisar patch grande",
        "inputs": {
            "diff_text": "\n".join(["+line"] * 4000),
            "objective": "review",
            "stack": "python",
        },
    }

    with TestClient(app) as client:
        response = client.post("/scenarios/run", json=payload, headers={"X-API-Key": _api_key()})

    assert response.status_code == 200


def test_scenarios_run_rejects_patch_review_without_diff_text() -> None:
    payload = {
        "project_id": "p-limits",
        "scenario_id": "patch_review",
        "objective": "revisar patch",
        "inputs": {
            "objective": "review",
            "stack": "python",
        },
    }

    with TestClient(app) as client:
        response = client.post("/scenarios/run", json=payload, headers={"X-API-Key": _api_key()})

    assert response.status_code == 400
    assert "diff_text" in response.json()["detail"]


def test_scenarios_run_rejects_code_analysis_without_files() -> None:
    payload = {
        "project_id": "p-limits",
        "scenario_id": "code_analysis",
        "objective": "analisar",
        "inputs": {
            "stack": "python",
            "objective": "analisar",
        },
    }

    with TestClient(app) as client:
        response = client.post("/scenarios/run", json=payload, headers={"X-API-Key": _api_key()})

    assert response.status_code == 400
    assert "files" in response.json()["detail"]


def test_scenarios_run_rejects_invalid_files_shape() -> None:
    payload = {
        "project_id": "p-limits",
        "scenario_id": "code_analysis",
        "objective": "analisar",
        "inputs": {
            "stack": "python",
            "objective": "analisar",
            "files": [{"path": "src/app.py"}],
        },
    }

    with TestClient(app) as client:
        response = client.post("/scenarios/run", json=payload, headers={"X-API-Key": _api_key()})

    assert response.status_code == 400
    assert "path and content" in response.json()["detail"]


def test_scenarios_run_rejects_files_with_wrong_type() -> None:
    payload = {
        "project_id": "p-limits",
        "scenario_id": "code_analysis",
        "objective": "analisar",
        "inputs": {
            "stack": "python",
            "objective": "analisar",
            "files": "src/app.py",
        },
    }

    with TestClient(app) as client:
        response = client.post("/scenarios/run", json=payload, headers={"X-API-Key": _api_key()})

    assert response.status_code == 400
    assert "files must" in response.json()["detail"]


def test_scenarios_run_rejects_repo_hydration_above_per_file_limit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "huge.py").write_text("x" * 200_000, encoding="utf-8")
    payload = {
        "project_id": "p-limits",
        "scenario_id": "refactor_suggestion",
        "objective": "analisar",
        "inputs": {
            "stack": "python",
            "objective": "analisar",
            "additional_instructions": "modularizar",
            "repo_path": str(repo),
            "file_pattern": "**/*.py",
            "repo_enrichment": {"enabled": True},
        },
    }

    with TestClient(app) as client:
        response = client.post("/scenarios/run", json=payload, headers={"X-API-Key": _api_key()})

    assert response.status_code == 400
    assert "max allowed size" in response.json()["detail"]
