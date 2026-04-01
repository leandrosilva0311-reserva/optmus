from dataclasses import dataclass

from optimus_backend.domain.entities import MemoryEntry
from optimus_backend.domain.ports import MemoryRepository


@dataclass(slots=True)
class ContextItem:
    content: str
    score: float
    reason: str


@dataclass(slots=True)
class ContextPayload:
    objective: str
    items: list[ContextItem]


class ContextBuilder:
    def __init__(self, memory_repository: MemoryRepository) -> None:
        self._memory_repository = memory_repository

    def build(self, project_id: str, objective: str, limit: int = 8) -> ContextPayload:
        approved = self._memory_repository.list_for_project(project_id, status="approved")
        ranked = sorted((self._to_item(entry, objective) for entry in approved), key=lambda i: i.score, reverse=True)
        return ContextPayload(objective=objective, items=ranked[:limit])

    @staticmethod
    def _to_item(entry: MemoryEntry, objective: str) -> ContextItem:
        overlap = len(set(objective.lower().split()) & set(entry.content.lower().split()))
        score = overlap + entry.confidence
        reason = f"overlap={overlap}, confidence={entry.confidence:.2f}, source={entry.source}"
        return ContextItem(content=entry.content, score=score, reason=reason)
