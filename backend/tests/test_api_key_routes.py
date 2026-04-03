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
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    dependencies.get_api_key_repository.cache_clear()
    dependencies.get_api_key_use_case.cache_clear()
    config.app_env = prev_env


def _admin_user() -> dict[str, str]:
    return {"auth_type": "user", "user_id": "u-admin", "role": "admin", "session_id": "s-1", "checked_at": "2026-01-01T00:00:00Z"}


def test_create_list_revoke_rotate_api_key_routes() -> None:
    app.dependency_overrides[dependencies.get_current_user] = _admin_user

    with TestClient(app) as client:
        created = client.post("/api-keys", json={"project_id": "p-1", "name": "sdk", "scopes": ["billing:read"]})
        assert created.status_code == 200
        created_body = created.json()
        assert "key" in created_body
        key_id = created_body["item"]["id"]

        listed = client.get("/api-keys", params={"project_id": "p-1"})
        assert listed.status_code == 200
        assert len(listed.json()) == 1
        assert listed.json()[0]["id"] == key_id

        revoked = client.post(f"/api-keys/{key_id}/revoke")
        assert revoked.status_code == 200
        assert revoked.json()["status"] == "revoked"

        rotated = client.post(f"/api-keys/{key_id}/rotate")
        assert rotated.status_code == 200
        assert rotated.json()["item"]["id"] != key_id
        assert "key" in rotated.json()
