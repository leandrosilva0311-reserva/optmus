import json
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
from optimus_backend.core.tooling.models import ToolExecutionEnvelope, ToolExecutionRequest
from optimus_backend.settings.config import config


def _extract_scenario_inputs(execution_id: str, audit_events: list) -> dict[str, str]:
    for event in reversed(audit_events):
        if event.event_type != "scenario_inputs":
            continue
        try:
            payload = json.loads(event.message)
            return {str(k): str(v) for k, v in payload.items()}
        except Exception:
            return {}
    return {}


def _scenario_tool_calls(record, inputs: dict[str, str], tool_executor) -> list[ToolExecutionEnvelope]:
    calls: list[tuple[str, dict[str, str]]] = []
    if record.scenario_id == "queue_health":
        calls.append(("queue_inspection", inputs))
    elif record.scenario_id == "incident_timeline_reconstruction":
        calls.append(("log_correlation", inputs))
        calls.append(("http", {"url": "https://example.com", "method": "GET"}))
    elif record.scenario_id == "checkout_flow_validation":
        calls.append(("log_correlation", inputs))
        calls.append(("queue_inspection", inputs))
        calls.append(("http", {"url": "https://example.com/checkout", "method": "GET"}))
    else:  # public_api_health and legacy aliases
        calls.append(("log_correlation", inputs))
        calls.append(("queue_inspection", inputs))

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


def _build_business_block(record, envelopes: list[ToolExecutionEnvelope], steps_used: int) -> dict[str, str]:
    blocked = [e for e in envelopes if e.status != "ok"]
    if blocked:
        return {
            "operational_impact": "Monitoramento parcial: há dependências externas indisponíveis para diagnóstico completo.",
            "commercial_impact": "Risco moderado de degradação de SLA e aumento de tickets de suporte.",
            "severity": "medium",
            "immediate_action": "Escalar dependência externa e executar fallback operacional enquanto o diagnóstico é concluído.",
            "suggested_owner": "OpsAgent",
        }

    if record.scenario_id == "queue_health":
        return {
            "operational_impact": f"Saúde de fila avaliada com sucesso em {steps_used} etapas de execução.",
            "commercial_impact": "Sem impacto comercial imediato; cenário útil para prevenção de backlog crítico.",
            "severity": "low",
            "immediate_action": "Manter monitoramento e configurar alerta para crescimento de oldest_job_age.",
            "suggested_owner": "OpsAgent",
        }

    if record.scenario_id == "checkout_flow_validation":
        return {
            "operational_impact": "Fluxo de checkout validado com verificação de consistência entre sinais de ordem e fila.",
            "commercial_impact": "Redução de risco de perda de conversão por falhas silenciosas no checkout.",
            "severity": "medium",
            "immediate_action": "Priorizar correção de inconsistências de checkout e acompanhar taxa de conversão nas próximas 24h.",
            "suggested_owner": "QAAgent",
        }

    if record.scenario_id == "incident_timeline_reconstruction":
        return {
            "operational_impact": "Linha do tempo do incidente consolidada para acelerar análise e contenção.",
            "commercial_impact": "Melhora comunicação com clientes afetados e reduz incerteza em incidentes críticos.",
            "severity": "medium",
            "immediate_action": "Executar postmortem curto com responsáveis e aplicar contenções imediatas identificadas.",
            "suggested_owner": "AnalystAgent",
        }

    return {
        "operational_impact": f"API pública validada ponta a ponta com correlação de logs e inspeção de fila ({steps_used} etapas).",
        "commercial_impact": "Fluxo principal operando dentro de parâmetros esperados, reduzindo risco de churn por indisponibilidade.",
        "severity": "low",
        "immediate_action": "Continuar monitoramento periódico e manter playbook de resposta rápida ativo.",
        "suggested_owner": "BackendAgent",
    }


def run_execution_job(ctx: dict, execution_id: str) -> None:
    _ = ctx
    executions, subtasks_repo, audit, _, _, _, _, locks, _ = get_repositories()
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
                business_block = _build_business_block(record, tool_envelopes, steps_used)
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
        business_block = _build_business_block(record, tool_envelopes, steps_used)
        audit.append(build_event(execution_id, "business_block", json.dumps(business_block, sort_keys=True)))
        finalize.complete(execution_id, summary=summary, duration_ms=duration, project_id=record.project_id)
    except Exception as exc:  # pragma: no cover
        duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
        finalize.fail(execution_id, message=str(exc), duration_ms=duration)
    finally:
        locks.release(lock_key)


class WorkerSettings:
    functions = [run_execution_job]
