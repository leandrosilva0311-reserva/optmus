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
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    dependencies.get_api_key_repository.cache_clear()
    dependencies.get_api_key_use_case.cache_clear()
    dependencies.get_repositories.cache_clear()
    config.app_env = prev_env


def test_get_current_user_accepts_x_api_key() -> None:
    use_case = dependencies.get_api_key_use_case()
    created = use_case.create_key("project-x", "sdk", ["admin:read"])  # noqa: F841

    with TestClient(app) as client:
        response = client.get("/agents/catalog", headers={"X-API-Key": created.plaintext_key})

    assert response.status_code == 200


def test_get_current_user_accepts_bearer_api_key() -> None:
    use_case = dependencies.get_api_key_use_case()
    created = use_case.create_key("project-x", "sdk", ["admin:read"])  # noqa: F841

    with TestClient(app) as client:
        response = client.get("/agents/catalog", headers={"Authorization": f"Bearer {created.plaintext_key}"})

    assert response.status_code == 200
