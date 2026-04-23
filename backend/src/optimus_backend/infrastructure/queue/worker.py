from dataclasses import replace
from datetime import UTC, datetime

from optimus_backend.api.dependencies import (
    get_engine,
    get_finalize_execution_use_case,
    get_repositories,
    get_tool_executor,
)
from optimus_backend.application.use_cases.start_execution import build_event
from optimus_backend.core.budget.enforcer import BudgetEnforcer, BudgetState
from optimus_backend.core.tooling.models import ToolExecutionRequest
from optimus_backend.settings.config import config


async def run_execution_job(ctx: dict, execution_id: str) -> None:
    _ = ctx
    executions, subtasks_repo, audit, _, _, _, _, locks = get_repositories()
    finalize = get_finalize_execution_use_case()
    engine = get_engine()
    tool_executor = get_tool_executor()
    budget = BudgetEnforcer()

    lock_key = f"execution:{execution_id}"
    if not locks.acquire(lock_key, ttl_seconds=config.lock_ttl_seconds):
        audit.append(build_event(execution_id, "lock_skipped", "Execution skipped because lock was already acquired"))
        return

    record = executions.get(execution_id)
    if record is None:
        locks.release(lock_key)
        return

    started = datetime.now(UTC)
    handoffs = 0
    try:
        finalize.mark_running(execution_id)

        subtasks = list(subtasks_repo.list_by_execution(execution_id))
        done_agents: set[str] = set()
        steps_used = 0
        tool_calls_used = 0

        for subtask in subtasks:
            if any(dep not in done_agents for dep in subtask.depends_on):
                continue

            handoffs += 1
            if handoffs > 3:
                audit.append(build_event(execution_id, "handoff_cutoff", "max_handoffs_reached"))
                break

            subtask = replace(subtask, status="running", updated_at=datetime.now(UTC), handoff_reason="dependency_satisfied")
            subtasks_repo.update(subtask)
            finalize.mark_subtask_event(execution_id, subtask, "subtask_started", "running")
            steps_used += 1

            tool_result = tool_executor.execute(
                ToolExecutionRequest(
                    execution_id=execution_id,
                    project_id=record.project_id,
                    tool_name="terminal",
                    payload={"command": "echo safe_tool_probe", "token": "secret-should-hide"},
                )
            )
            tool_calls_used += 1
            audit.append(
                build_event(
                    execution_id,
                    "tool_envelope",
                    f"tool=terminal status={tool_result.status} duration_ms={tool_result.duration_ms} truncated={tool_result.truncated} blocked_reason={tool_result.blocked_reason} payload_hash={tool_result.payload_hash}",
                )
            )

            elapsed = int((datetime.now(UTC) - started).total_seconds() * 1000)
            ok, cutoff_reason = budget.check(
                BudgetState(steps_used=steps_used, tool_calls_used=tool_calls_used, duration_ms=elapsed),
                max_steps=record.max_steps,
                max_tool_calls=record.max_tool_calls,
                max_duration_ms=record.max_duration_ms,
            )
            if not ok:
                bounded_summary = f"bounded_completion cutoff={cutoff_reason} steps={steps_used} tool_calls={tool_calls_used} elapsed_ms={elapsed}"
                finalize.complete(execution_id, summary=bounded_summary, duration_ms=elapsed, project_id=record.project_id)
                current = executions.get(execution_id)
                if current is not None:
                    executions.update(replace(current, status="bounded_completion", summary=bounded_summary, duration_ms=elapsed))
                audit.append(build_event(execution_id, "budget_cutoff", cutoff_reason or "unknown"))
                return

            result = await engine._orchestrator.run(subtask.agent, subtask.title)
            status = "completed"
            if subtask.agent == "analyst" and not result.execution_plan:
                status = "partial"
                audit.append(build_event(execution_id, "analyst_plan_invalid", "execution_plan missing"))

            subtask = replace(
                subtask,
                status=status,
                result_summary=result.diagnosis[:200],
                updated_at=datetime.now(UTC),
                attempt=subtask.attempt + 1,
            )
            subtasks_repo.update(subtask)
            finalize.mark_subtask_event(execution_id, subtask, "subtask_completed", status)
            done_agents.add(subtask.agent)

        duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
        summary = f"processed_subtasks={len(done_agents)} steps_used={steps_used} tool_calls={tool_calls_used}"
        finalize.complete(execution_id, summary=summary, duration_ms=duration, project_id=record.project_id)
    except Exception as exc:  # pragma: no cover
        duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
        finalize.fail(execution_id, message=str(exc), duration_ms=duration)
    finally:
        locks.release(lock_key)


class WorkerSettings:
    functions = [run_execution_job]
