import json
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from optimus_backend.api.dependencies import (
    get_engine,
    get_finalize_execution_use_case,
    get_repositories,
    get_tool_executor,
)
from optimus_backend.application.use_cases.start_execution import build_event
from optimus_backend.core.budget.enforcer import BudgetEnforcer, BudgetState
from optimus_backend.core.tooling.models import ToolExecutionEnvelope, ToolExecutionRequest
from optimus_backend.domain.entities import MemoryEntry
from optimus_backend.settings.config import config


def _extract_scenario_inputs(execution_id: str, audit_events: list) -> dict[str, object]:
    for event in reversed(audit_events):
        if event.event_type != "scenario_inputs":
            continue
        try:
            payload = json.loads(event.message)
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}
    return {}


def _scenario_tool_calls(record, inputs: dict[str, object], tool_executor) -> list[ToolExecutionEnvelope]:
    files = inputs.get("files", [])
    calls: list[tuple[str, dict[str, object]]] = []

    if record.scenario_id == "code_analysis":
        calls.append(("code_search", {"query": str(inputs.get("objective", "")), "files": files}))
        calls.append(("config_inspection", {"config_text": str(inputs.get("source_text", "{}"))}))
    elif record.scenario_id == "bug_diagnosis":
        calls.append(("log_analysis", {"log_text": str(inputs.get("observed_error", ""))}))
        calls.append(("code_search", {"query": str(inputs.get("observed_error", "")), "files": files}))
    elif record.scenario_id == "refactor_suggestion":
        calls.append(("code_search", {"query": str(inputs.get("objective", "")), "files": files}))
        calls.append(("config_inspection", {"config_text": str(inputs.get("additional_instructions", "{}"))}))
    elif record.scenario_id == "patch_review":
        calls.append(("diff_analysis", {"diff_text": str(inputs.get("diff_text", ""))}))
        calls.append(("log_analysis", {"log_text": str(inputs.get("observed_error", ""))}))
    else:
        calls.append(("log_analysis", {"log_text": str(inputs.get("observed_error", ""))}))

    envelopes: list[ToolExecutionEnvelope] = []
    for tool_name, payload in calls:
        envelopes.append(
            tool_executor.execute(
                ToolExecutionRequest(
                    execution_id=record.id,
                    project_id=record.project_id,
                    tool_name=tool_name,
                    payload=payload,
                )
            )
        )
    return envelopes


def _build_engineering_report(
    record,
    envelopes: list[ToolExecutionEnvelope],
    steps_used: int,
    generated_at: datetime,
) -> dict[str, object]:
    blocked = [e for e in envelopes if e.status != "ok"]

    execution_plan = [
        {
            "step_id": "s1",
            "title": "Confirmar diagnóstico",
            "description": "Validar hipótese principal com evidências coletadas",
            "expected_outcome": "Hipótese confirmada ou descartada com critério objetivo",
        },
        {
            "step_id": "s2",
            "title": "Aplicar recomendação prioritária",
            "description": "Executar mudança de menor risco e maior impacto",
            "expected_outcome": "Correção/ganho mensurável no componente-alvo",
        },
        {
            "step_id": "s3",
            "title": "Verificar regressão",
            "description": "Executar validações funcionais e técnicas pós-ação",
            "expected_outcome": "Estabilidade confirmada sem regressão crítica",
        },
    ]

    if blocked:
        return {
            "execution_id": record.id,
            "scenario_id": record.scenario_id,
            "diagnosis": "Execução parcial: ao menos uma capability retornou bloqueio/erro.",
            "evidence": [e.error or e.blocked_reason or "blocked" for e in blocked],
            "recommendations": [
                "Reexecutar cenário com payload válido para todas as capabilities necessárias.",
                "Revisar política de ferramentas e guardrails antes da próxima execução.",
            ],
            "risk_level": "high",
            "urgency": "high",
            "execution_plan": execution_plan,
            "generated_at": generated_at.isoformat(),
        }

    return {
        "execution_id": record.id,
        "scenario_id": record.scenario_id,
        "diagnosis": f"Scenario {record.scenario_id} completed with {len(envelopes)} capability checks.",
        "evidence": [e.output or e.error or "no_output" for e in envelopes],
        "recommendations": [
            "Priorizar alterações de baixo risco com rollback claro.",
            "Adicionar verificação automatizada para o ponto identificado.",
        ],
        "risk_level": "medium" if steps_used > 2 else "low",
        "urgency": "high" if record.scenario_id in {"bug_diagnosis", "patch_review"} else "medium",
        "execution_plan": execution_plan,
        "generated_at": generated_at.isoformat(),
    }


def _build_business_block(engineering_report: dict[str, object]) -> dict[str, object]:
    risk_to_severity = {"low": "low", "medium": "medium", "high": "high", "critical": "critical"}
    urgency_to_action = {
        "low": "Agendar melhoria incremental com monitoramento básico.",
        "medium": "Priorizar na próxima sprint com validação de impacto.",
        "high": "Executar ação corretiva ainda hoje com rollback definido.",
        "immediate": "Acionar resposta imediata e comunicação de incidente.",
    }
    urgency_to_owner = {
        "low": "engineering",
        "medium": "tech_lead",
        "high": "incident_commander",
        "immediate": "incident_commander",
    }
    urgency = str(engineering_report.get("urgency", "medium"))
    risk = str(engineering_report.get("risk_level", "medium"))
    return {
        "operational_impact": f"Scenario {engineering_report.get('scenario_id', 'unknown')} executado com diagnóstico técnico registrado.",
        "commercial_impact": "A resposta técnica reduz risco operacional e orienta priorização de entrega.",
        "severity": risk_to_severity.get(risk, "medium"),
        "immediate_action": urgency_to_action.get(urgency, urgency_to_action["medium"]),
        "suggested_owner": urgency_to_owner.get(urgency, urgency_to_owner["medium"]),
    }


def _persist_engineering_report_artifact(memory_repo, record, engineering_report: dict[str, object]) -> None:
    latest = memory_repo.latest_by_type(record.project_id, "engineering_report")
    version = (latest.version + 1) if latest else 1
    memory_repo.add(
        MemoryEntry(
            id=str(uuid4()),
            project_id=record.project_id,
            entry_type="engineering_report",
            source=record.id,
            confidence=0.95,
            content=json.dumps(engineering_report, sort_keys=True),
            status="approved",
            created_at=datetime.now(UTC),
            version=version,
            supersedes_id=latest.id if latest else None,
        )
    )


def run_execution_job(ctx: dict, execution_id: str) -> None:
    _ = ctx
    executions, subtasks_repo, audit, memory_repo, _, _, _, locks, _ = get_repositories()
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

        audit_events = list(audit.list_by_execution(execution_id))
        scenario_inputs = _extract_scenario_inputs(execution_id, audit_events)

        tool_envelopes = _scenario_tool_calls(record, scenario_inputs, tool_executor)
        for envelope in tool_envelopes:
            audit.append(
                build_event(
                    execution_id,
                    "tool_envelope",
                    f"status={envelope.status} duration_ms={envelope.duration_ms} truncated={envelope.truncated} blocked_reason={envelope.blocked_reason} payload_hash={envelope.payload_hash}",
                )
            )

        subtasks = list(subtasks_repo.list_by_execution(execution_id))
        done_agents: set[str] = set()
        steps_used = 0
        tool_calls_used = len(tool_envelopes)

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

            elapsed = int((datetime.now(UTC) - started).total_seconds() * 1000)
            ok, cutoff_reason = budget.check(
                BudgetState(steps_used=steps_used, tool_calls_used=tool_calls_used, duration_ms=elapsed),
                max_steps=record.max_steps,
                max_tool_calls=record.max_tool_calls,
                max_duration_ms=record.max_duration_ms,
            )
            if not ok:
                bounded_summary = f"bounded_completion cutoff={cutoff_reason} steps={steps_used} tool_calls={tool_calls_used} elapsed_ms={elapsed}"
                generated_at = datetime.now(UTC)
                engineering_report = _build_engineering_report(record, tool_envelopes, steps_used, generated_at)
                business_block = _build_business_block(engineering_report)
                audit.append(build_event(execution_id, "engineering_report", json.dumps(engineering_report, sort_keys=True)))
                _persist_engineering_report_artifact(memory_repo, record, engineering_report)
                audit.append(build_event(execution_id, "business_block", json.dumps(business_block, sort_keys=True)))
                finalize.complete(execution_id, summary=bounded_summary, duration_ms=elapsed, project_id=record.project_id)
                current = executions.get(execution_id)
                if current is not None:
                    executions.update(replace(current, status="bounded_completion", summary=bounded_summary, duration_ms=elapsed))
                audit.append(build_event(execution_id, "budget_cutoff", cutoff_reason or "unknown"))
                return

            result = engine._orchestrator.run(subtask.agent, subtask.title)
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
        generated_at = datetime.now(UTC)
        engineering_report = _build_engineering_report(record, tool_envelopes, steps_used, generated_at)
        business_block = _build_business_block(engineering_report)
        audit.append(build_event(execution_id, "engineering_report", json.dumps(engineering_report, sort_keys=True)))
        _persist_engineering_report_artifact(memory_repo, record, engineering_report)
        audit.append(build_event(execution_id, "business_block", json.dumps(business_block, sort_keys=True)))
        finalize.complete(execution_id, summary=summary, duration_ms=duration, project_id=record.project_id)
    except Exception as exc:  # pragma: no cover
        duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
        finalize.fail(execution_id, message=str(exc), duration_ms=duration)
    finally:
        locks.release(lock_key)


class WorkerSettings:
    functions = [run_execution_job]
