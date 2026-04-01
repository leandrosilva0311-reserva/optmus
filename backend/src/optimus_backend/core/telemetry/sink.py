from dataclasses import dataclass
from datetime import datetime, UTC


@dataclass(slots=True)
class TelemetryEvent:
    execution_id: str
    agent: str
    event_type: str
    message: str


class TelemetrySink:
    def __init__(self) -> None:
        self._events: list[TelemetryEvent] = []

    def emit(self, event: TelemetryEvent) -> None:
        self._events.append(event)

    def list_events(self, execution_id: str) -> list[TelemetryEvent]:
        return [e for e in self._events if e.execution_id == execution_id]

    @staticmethod
    def now_iso() -> str:
        return datetime.now(UTC).isoformat()
