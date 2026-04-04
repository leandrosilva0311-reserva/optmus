from dataclasses import dataclass


@dataclass(slots=True)
class Tenant:
    id: str
    name: str
    plan: str
    is_active: bool = True


@dataclass(slots=True)
class APIKey:
    id: str
    tenant_id: str
    label: str
    is_active: bool = True
