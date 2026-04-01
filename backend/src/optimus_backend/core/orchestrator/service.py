from optimus_backend.core.specialists.agents import BaseSpecialist, SpecialistResult


class Orchestrator:
    def __init__(self, specialists: dict[str, BaseSpecialist]) -> None:
        self._specialists = specialists

    def run(self, agent: str, objective: str) -> SpecialistResult:
        specialist = self._specialists.get(agent)
        if specialist is None:
            raise KeyError(f"agent '{agent}' not configured")
        return specialist.run(objective)
