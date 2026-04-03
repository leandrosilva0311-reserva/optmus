from optimus_backend.infrastructure.persistence.in_memory import InMemoryLockManager


def test_lock_manager_acquire_release_cycle() -> None:
    locks = InMemoryLockManager()

    first = locks.acquire("execution:abc", ttl_seconds=30)
    second = locks.acquire("execution:abc", ttl_seconds=30)
    locks.release("execution:abc")
    third = locks.acquire("execution:abc", ttl_seconds=30)

    assert first is True
    assert second is False
    assert third is True
