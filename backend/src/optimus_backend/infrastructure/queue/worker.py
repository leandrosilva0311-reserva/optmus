from dataclasses import replace
from datetime import UTC, datetime

from optimus_backend.api.dependencies import (
    get_engine,
    get_finalize_execution_use_case,
    get_repositories,
    get_tool_executor,
)
from optimus_backend.application.use_cases.start_execution import build_event
from optimus_backend.core.tooling.models import ToolExecutionRequest
from optimus_backend.settings.config import config


def run_execution_job(ctx: dict, execution_id: str) -> None:
    _ = ctx
    executions, subtasks_repo, audit, _, _, _, _, locks = get_repositories()
    finalize = get_finalize_execution_use_case()
    engine = get_engine()
    tool_executor = get_tool_executor()

    lock_key = f"execution:{execution_id}"
    if not locks.acquire(lock_key, ttl_seconds=config.lock_ttl_seconds):
        audit.append(build_event(execution_id, "lock_skipped", "Execution skipped because lock was already acquired"))
        return

    record = executions.get(execution_id)
    if record is None:
        locks.release(lock_key)
        return

    started = datetime.now(UTC)
    try:
        finalize.mark_running(execution_id)

        subtasks = list(subtasks_repo.list_by_execution(execution_id))
        done_agents: set[str] = set()

        for subtask in subtasks:
            if any(dep not in done_agents for dep in subtask.depends_on):
                continue

            subtask = replace(subtask, status="running", updated_at=datetime.now(UTC))
            subtasks_repo.update(subtask)
            finalize.mark_subtask_event(execution_id, subtask, "subtask_started", "running")

            tool_result = tool_executor.execute(
                ToolExecutionRequest(
                    execution_id=execution_id,
                    tool_name="terminal",
                    payload={"command": "echo safe_tool_probe"},
                )
            )
            audit.append(
                build_event(
                    execution_id,
                    "tool_envelope",
                    f"tool=terminal status={tool_result.status} duration_ms={tool_result.duration_ms} truncated={tool_result.truncated} error={tool_result.error}",
                )
            )

            result = engine._orchestrator.run(subtask.agent, subtask.title)
            subtask = replace(
                subtask,
                status="completed",
                result_summary=result.output[:200],
                updated_at=datetime.now(UTC),
            )
            subtasks_repo.update(subtask)
            finalize.mark_subtask_event(execution_id, subtask, "subtask_completed", "completed")
            done_agents.add(subtask.agent)

        duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
        summary = f"processed_subtasks={len(done_agents)}"
        finalize.complete(execution_id, summary=summary, duration_ms=duration, project_id=record.project_id)
    except Exception as exc:  # pragma: no cover
        duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
        finalize.fail(execution_id, message=str(exc), duration_ms=duration)
    finally:
        locks.release(lock_key)


class WorkerSettings:
    functions = [run_execution_job]
