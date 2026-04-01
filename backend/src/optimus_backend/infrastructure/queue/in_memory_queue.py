class InMemoryJobQueue:
    def __init__(self) -> None:
        self.enqueued: list[str] = []

    def enqueue_execution(self, execution_id: str) -> None:
        self.enqueued.append(execution_id)
