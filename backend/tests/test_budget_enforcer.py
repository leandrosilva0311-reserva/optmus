from optimus_backend.core.budget.enforcer import BudgetEnforcer, BudgetState


def test_budget_priority_when_multiple_exceeded() -> None:
    enforcer = BudgetEnforcer()
    ok, reason = enforcer.check(
        BudgetState(steps_used=100, tool_calls_used=100, duration_ms=999999),
        max_steps=10,
        max_tool_calls=10,
        max_duration_ms=1000,
    )
    assert ok is False
    assert reason == "max_duration_ms"
