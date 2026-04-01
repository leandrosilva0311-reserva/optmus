from dataclasses import dataclass, field


@dataclass(slots=True)
class MemoryStore:
    short_term: dict[str, list[str]] = field(default_factory=dict)
    persistent: dict[str, list[str]] = field(default_factory=dict)

    def add_short_term(self, execution_id: str, item: str) -> None:
        self.short_term.setdefault(execution_id, []).append(item)

    def add_persistent(self, project_id: str, item: str) -> None:
        self.persistent.setdefault(project_id, []).append(item)
