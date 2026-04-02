from collections.abc import Iterable

SCENARIOS_RUN = "scenarios:run"
BILLING_READ = "billing:read"
USAGE_READ = "usage:read"
ADMIN_READ = "admin:read"

VALID_API_KEY_SCOPES: frozenset[str] = frozenset({
    SCENARIOS_RUN,
    BILLING_READ,
    USAGE_READ,
    ADMIN_READ,
})


def validate_scopes(scopes: Iterable[str]) -> list[str]:
    normalized = sorted({scope.strip() for scope in scopes if scope and scope.strip()})
    unknown = [scope for scope in normalized if scope not in VALID_API_KEY_SCOPES]
    if unknown:
        raise ValueError(f"invalid scopes: {', '.join(unknown)}")
    return normalized
