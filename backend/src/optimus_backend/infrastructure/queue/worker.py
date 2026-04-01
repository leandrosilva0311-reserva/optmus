from datetime import UTC, datetime

from optimus_backend.api.dependencies import get_engine, get_finalize_execution_use_case, get_repositories
from optimus_backend.application.use_cases.start_execution import build_event
from optimus_backend.settings.config import config


def run_execution_job(ctx: dict, execution_id: str) -> None:
    _ = ctx
    executions, audit, _, _, _, locks = get_repositories()
    finalize = get_finalize_execution_use_case()
    engine = get_engine()

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
        result = engine.execute(objective=record.objective, agent=record.agent)
        duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
        finalize.complete(execution_id, summary=result.summary, duration_ms=duration)
    except Exception as exc:  # pragma: no cover
        duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
        finalize.fail(execution_id, message=str(exc), duration_ms=duration)
    finally:
        locks.release(lock_key)


class WorkerSettings:
    functions = [run_execution_job]
