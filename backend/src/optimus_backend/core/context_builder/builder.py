from dataclasses import dataclass
from optimus_backend.core.memory.store import MemoryStore


@dataclass(slots=True)
class ContextPayload:
    objective: str
    memory_items: list[str]


class ContextBuilder:
    def __init__(self, memory: MemoryStore) -> None:
        self._memory = memory

    def build(self, execution_id: str, objective: str) -> ContextPayload:
        memory_items = self._memory.short_term.get(execution_id, [])
        return ContextPayload(objective=objective, memory_items=memory_items)
