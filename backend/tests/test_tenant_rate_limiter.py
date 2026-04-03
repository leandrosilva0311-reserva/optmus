from optimus_backend.infrastructure.tenancy.in_memory import InMemoryTenantRateLimiter


def test_tenant_rate_limiter_blocks_after_limit() -> None:
    limiter = InMemoryTenantRateLimiter()

    assert limiter.allow("tenant-a", limit=2)
    assert limiter.allow("tenant-a", limit=2)
    assert limiter.allow("tenant-a", limit=2) is False
