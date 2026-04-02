import pytest

pytest.importorskip("fastapi")

from optimus_backend.api.dependencies import get_billing_command_model, get_billing_read_model, get_billing_store, get_usage_meter
from optimus_backend.infrastructure.billing.in_memory_billing_store import InMemoryBillingStore
from optimus_backend.infrastructure.billing.in_memory_usage_meter import InMemoryUsageMeter
from optimus_backend.infrastructure.billing.postgres_billing_store import PostgresBillingStore
from optimus_backend.infrastructure.billing.postgres_usage_meter import PostgresUsageMeter
from optimus_backend.settings.config import config


def test_get_usage_meter_returns_in_memory_for_test_env() -> None:
    config.app_env = "test"
    get_usage_meter.cache_clear()
    meter = get_usage_meter()
    assert isinstance(meter, InMemoryUsageMeter)


def test_get_usage_meter_returns_postgres_for_non_test_env() -> None:
    config.app_env = "development"
    get_usage_meter.cache_clear()
    meter = get_usage_meter()
    assert isinstance(meter, PostgresUsageMeter)


def test_get_billing_models_return_in_memory_for_test_env() -> None:
    config.app_env = "test"
    get_billing_store.cache_clear()
    get_billing_read_model.cache_clear()
    get_billing_command_model.cache_clear()
    read_model = get_billing_read_model()
    command_model = get_billing_command_model()
    assert isinstance(read_model, InMemoryBillingStore)
    assert isinstance(command_model, InMemoryBillingStore)


def test_get_billing_models_return_postgres_for_non_test_env() -> None:
    config.app_env = "development"
    get_billing_store.cache_clear()
    get_billing_read_model.cache_clear()
    get_billing_command_model.cache_clear()
    read_model = get_billing_read_model()
    command_model = get_billing_command_model()
    assert isinstance(read_model, PostgresBillingStore)
    assert isinstance(command_model, PostgresBillingStore)
