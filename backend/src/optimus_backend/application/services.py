from optimus_backend.core.agent_core.engine import AgentEngine, ExecutionResult


class TaskService:
    def __init__(self, engine: AgentEngine) -> None:
        self._engine = engine

    async def run_task(self, objective: str, agent: str) -> ExecutionResult:
        return await self._engine.execute(objective=objective, agent=agent)
