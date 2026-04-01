from optimus_backend.core.execution_guard.guard import ExecutionGuard
from optimus_backend.core.policy.engine import PolicyEngine
from optimus_backend.core.tooling.executor import ToolExecutor
from optimus_backend.core.tooling.models import ToolExecutionRequest
from optimus_backend.infrastructure.tools.terminal_tool import TerminalTool


def test_tool_executor_envelope_and_policy_guard_order() -> None:
    executor = ToolExecutor(
        tools={"terminal": TerminalTool(allowed_commands={"echo"}, timeout_seconds=2)},
        policy=PolicyEngine(allowed_tools={"terminal"}),
        guard=ExecutionGuard(),
    )

    result = executor.execute(
        ToolExecutionRequest(execution_id="e1", tool_name="terminal", payload={"command": "echo hello"})
    )

    assert result.status == "ok"
    assert result.duration_ms >= 0
    assert result.error is None
    assert "hello" in (result.output or "")


def test_tool_executor_denies_not_allowed_tool() -> None:
    executor = ToolExecutor(tools={}, policy=PolicyEngine(allowed_tools={"filesystem"}), guard=ExecutionGuard())
    result = executor.execute(ToolExecutionRequest(execution_id="e2", tool_name="terminal", payload={"command": "echo x"}))
    assert result.status == "denied"
