import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from optimus_backend.api.dependencies import get_auth_use_case
from optimus_backend.application.use_cases.authenticate import AuthenticateUserUseCase
from optimus_backend.infrastructure.persistence.in_memory import InMemorySessionRepository, InMemoryUserRepository
from optimus_backend.main import app


def _auth_use_case_with_users(users: list) -> AuthenticateUserUseCase:
    return AuthenticateUserUseCase(users=InMemoryUserRepository(users), sessions=InMemorySessionRepository())


def test_login_invalid_payload_returns_422() -> None:
    client = TestClient(app)

    response = client.post("/auth/login", json={"email": "invalid-email", "password": "123"})

    assert response.status_code == 422


def test_login_unknown_credentials_returns_401_not_500() -> None:
    app.dependency_overrides[get_auth_use_case] = lambda: _auth_use_case_with_users([])
    client = TestClient(app)

    response = client.post("/auth/login", json={"email": "test@optimus.com", "password": "12345678"})

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid credentials"

    app.dependency_overrides.clear()
