from datetime import UTC, datetime

from optimus_backend.domain.entities import MemoryEntry
from optimus_backend.infrastructure.persistence.in_memory import InMemoryMemoryRepository


def test_memory_latest_by_type() -> None:
    repo = InMemoryMemoryRepository()
    repo.add(
        MemoryEntry(
            id="m1",
            project_id="p1",
            entry_type="decision",
            source="test",
            confidence=0.5,
            content="old",
            status="approved",
            created_at=datetime.now(UTC),
            version=1,
        )
    )
    repo.add(
        MemoryEntry(
            id="m2",
            project_id="p1",
            entry_type="decision",
            source="test",
            confidence=0.8,
            content="new",
            status="pending",
            created_at=datetime.now(UTC),
            version=2,
            supersedes_id="m1",
        )
    )
    latest = repo.latest_by_type("p1", "decision")
    assert latest is not None
    assert latest.id == "m2"
