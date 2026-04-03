from optimus_backend.application.use_cases.resolve_tenant import ResolveTenantByApiKeyUseCase
from optimus_backend.core.tenancy.security import hash_api_key
from optimus_backend.domain.entities import APIKeyRecord, TenantRecord
from optimus_backend.infrastructure.tenancy.in_memory import InMemoryAPIKeyRepository, InMemoryTenantRepository


def test_resolve_tenant_by_api_key() -> None:
    tenants = InMemoryTenantRepository([TenantRecord(id="t1", name="Acme", plan="starter", is_active=True)])
    api_keys = InMemoryAPIKeyRepository(
        [APIKeyRecord(id="k1", tenant_id="t1", key_hash=hash_api_key("acme-key"), label="primary", is_active=True)]
    )

    resolved = ResolveTenantByApiKeyUseCase(api_keys=api_keys, tenants=tenants).execute("acme-key")

    assert resolved.tenant.id == "t1"
    assert resolved.api_key.id == "k1"


def test_resolve_tenant_rejects_invalid_key() -> None:
    tenants = InMemoryTenantRepository([TenantRecord(id="t1", name="Acme", plan="starter", is_active=True)])
    api_keys = InMemoryAPIKeyRepository(
        [APIKeyRecord(id="k1", tenant_id="t1", key_hash=hash_api_key("acme-key"), label="primary", is_active=True)]
    )

    try:
        ResolveTenantByApiKeyUseCase(api_keys=api_keys, tenants=tenants).execute("wrong-key")
    except PermissionError as exc:
        assert str(exc) == "invalid api key"
    else:
        raise AssertionError("PermissionError expected")
