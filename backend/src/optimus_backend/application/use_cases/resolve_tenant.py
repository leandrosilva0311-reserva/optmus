from dataclasses import dataclass

from optimus_backend.core.tenancy.models import APIKey, Tenant
from optimus_backend.domain.ports import APIKeyRepository, TenantRepository


@dataclass(slots=True)
class ResolvedTenant:
    tenant: Tenant
    api_key: APIKey


class ResolveTenantByApiKeyUseCase:
    def __init__(self, api_keys: APIKeyRepository, tenants: TenantRepository) -> None:
        self._api_keys = api_keys
        self._tenants = tenants

    def execute(self, raw_api_key: str) -> ResolvedTenant:
        record = self._api_keys.find_by_raw_key(raw_api_key)
        if record is None or not record.is_active:
            raise PermissionError("invalid api key")

        tenant_record = self._tenants.find_by_id(record.tenant_id)
        if tenant_record is None or not tenant_record.is_active:
            raise PermissionError("inactive tenant")

        return ResolvedTenant(
            tenant=Tenant(
                id=tenant_record.id,
                name=tenant_record.name,
                plan=tenant_record.plan,
                is_active=tenant_record.is_active,
            ),
            api_key=APIKey(
                id=record.id,
                tenant_id=record.tenant_id,
                label=record.label,
                is_active=record.is_active,
            ),
        )
