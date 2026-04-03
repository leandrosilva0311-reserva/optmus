import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from optimus_backend.main import app
from optimus_backend.settings.config import config


def test_middleware_requires_api_key() -> None:
    client = TestClient(app)
    response = client.get("/executions/")
    assert response.status_code == 401
    assert response.json()["detail"] == "missing api key"


def test_middleware_allows_exempt_health_route_without_api_key() -> None:
    client = TestClient(app)
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_middleware_accepts_valid_api_key() -> None:
    client = TestClient(app)
    response = client.get("/executions/", headers={"X-API-Key": config.default_tenant_api_key})
    assert response.status_code == 401
    assert response.json()["detail"] == "missing session"
