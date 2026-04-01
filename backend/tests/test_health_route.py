import pytest

pytest.importorskip("fastapi")

from optimus_backend.main import app


def test_app_has_core_routes() -> None:
    paths = {route.path for route in app.routes}
    assert "/health/" in paths
    assert "/auth/login" in paths
    assert "/executions/" in paths
