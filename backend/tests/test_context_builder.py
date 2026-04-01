from datetime import UTC, datetime

from optimus_backend.core.context_builder.builder import ContextBuilder
from optimus_backend.domain.entities import MemoryEntry
from optimus_backend.infrastructure.persistence.in_memory import InMemoryMemoryRepository


def test_context_builder_ranks_and_explains() -> None:
    memory = InMemoryMemoryRepository()
    memory.add(
        MemoryEntry(
            id="m1",
            project_id="p1",
            entry_type="fact",
            source="ops",
            confidence=0.9,
            content="deploy falhou por timeout de banco",
            status="approved",
            created_at=datetime.now(UTC),
        )
    )
    memory.add(
        MemoryEntry(
            id="m2",
            project_id="p1",
            entry_type="fact",
            source="qa",
            confidence=0.2,
            content="UI com problema visual",
            status="approved",
            created_at=datetime.now(UTC),
        )
    )

    context = ContextBuilder(memory).build(project_id="p1", objective="investigar timeout de banco")
    assert len(context.items) == 2
    assert "confidence" in context.items[0].reason
