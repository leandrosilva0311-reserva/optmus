from optimus_backend.core.provider.kaiso import KaisoLogCorrelationProvider


class InMemoryKaisoLogCorrelationProvider:
    def correlate(
        self,
        *,
        request_id: str,
        execution_id: str,
        order_id: str,
        restaurant_id: str,
        time_window_start: str,
        time_window_end: str,
    ) -> str:
        return (
            "correlation_ok "
            f"request_id={request_id} execution_id={execution_id} order_id={order_id} "
            f"restaurant_id={restaurant_id} time_window={time_window_start}..{time_window_end}"
        )


class KaisoLogCorrelationTool:
    name = "kaiso_log_correlation"

    def __init__(self, provider: KaisoLogCorrelationProvider) -> None:
        self._provider = provider

    def run(self, payload: dict) -> tuple[str, bool]:
        required = (
            "request_id",
            "execution_id",
            "order_id",
            "restaurant_id",
            "time_window_start",
            "time_window_end",
        )
        missing = [key for key in required if not payload.get(key)]
        if missing:
            raise ValueError(f"missing required correlation keys: {', '.join(missing)}")
        output = self._provider.correlate(
            request_id=str(payload["request_id"]),
            execution_id=str(payload["execution_id"]),
            order_id=str(payload["order_id"]),
            restaurant_id=str(payload["restaurant_id"]),
            time_window_start=str(payload["time_window_start"]),
            time_window_end=str(payload["time_window_end"]),
        )
        return output, False
