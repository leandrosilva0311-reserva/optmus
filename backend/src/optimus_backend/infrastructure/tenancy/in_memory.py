from optimus_backend.core.tenancy.security import hash_api_key
from optimus_backend.domain.entities import APIKeyRecord, TenantRecord


class InMemoryTenantRepository:
    def __init__(self, tenants: list[TenantRecord]) -> None:
        self._items = {tenant.id: tenant for tenant in tenants}

    def find_by_id(self, tenant_id: str) -> TenantRecord | None:
        return self._items.get(tenant_id)


class InMemoryAPIKeyRepository:
    def __init__(self, api_keys: list[APIKeyRecord]) -> None:
        self._items = {record.key_hash: record for record in api_keys}

    def find_by_raw_key(self, raw_key: str) -> APIKeyRecord | None:
        return self._items.get(hash_api_key(raw_key))


class InMemoryTenantRateLimiter:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def allow(self, tenant_id: str, limit: int, ttl_seconds: int = 60) -> bool:
        _ = ttl_seconds
        key = f"tenant:{tenant_id}"
        self._counts[key] = self._counts.get(key, 0) + 1
        return self._counts[key] <= limit
