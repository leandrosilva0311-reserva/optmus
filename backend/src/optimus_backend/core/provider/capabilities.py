from typing import Protocol


class LogCorrelationProvider(Protocol):
    def correlate(
        self,
        *,
        request_id: str,
        execution_id: str,
        order_id: str,
        restaurant_id: str,
        time_window_start: str,
        time_window_end: str,
    ) -> str: ...


class QueueInspectionProvider(Protocol):
    def inspect(self, *, restaurant_id: str, time_window_start: str, time_window_end: str) -> dict[str, float | int]: ...
