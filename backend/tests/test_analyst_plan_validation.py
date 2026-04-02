from optimus_backend.core.provider.base import MockProvider
from optimus_backend.core.specialists.agents import AnalystAgent


def test_analyst_agent_generates_execution_plan() -> None:
    result = AnalystAgent(MockProvider()).run("triage failure")
    assert len(result.execution_plan) > 0
