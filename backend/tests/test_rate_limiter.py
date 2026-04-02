from optimus_backend.infrastructure.persistence.in_memory import InMemoryRateLimiter


def test_rate_limiter_blocks_after_limit() -> None:
    rl = InMemoryRateLimiter()
    assert rl.allow("p1", "terminal", project_limit=2, tool_limit=2)
    assert rl.allow("p1", "terminal", project_limit=2, tool_limit=2)
    assert rl.allow("p1", "terminal", project_limit=2, tool_limit=2) is False
