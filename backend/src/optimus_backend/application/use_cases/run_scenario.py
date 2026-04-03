import json
from dataclasses import dataclass

from optimus_backend.application.scenarios.repo_enrichment import enrich_repo_inputs_for_scenario, to_audit_payload
from optimus_backend.application.scenarios.aliases import resolve_scenario_id
from optimus_backend.application.use_cases.start_execution import StartExecutionUseCase, build_event, build_idempotency_key
from optimus_backend.core.scenarios.catalog import ScenarioCatalog
from optimus_backend.core.source_connectors.protocols import SourceConnector
from optimus_backend.core.usage.metering import UsageSnapshot, warning_for_ratio
from optimus_backend.domain.ports import AuditRepository, BillingReadModel, ExecutionRepository, UsageMeter


@dataclass(slots=True)
class RunScenarioResult:
    execution_id: str
    status: str
    reused: bool
    usage: UsageSnapshot
    scenario_id: str
    deprecated_alias_used: bool = False


class RunScenarioUseCase:
    def __init__(
        self,
        start_execution: StartExecutionUseCase,
        executions: ExecutionRepository,
        catalog: ScenarioCatalog,
        audit: AuditRepository,
        usage_meter: UsageMeter,
        billing_read_model: BillingReadModel,
        source_connector_factory: type[SourceConnector] | None = None,
    ) -> None:
        self._start_execution = start_execution
        self._executions = executions
        self._catalog = catalog
        self._audit = audit
        self._usage_meter = usage_meter
        self._billing_read_model = billing_read_model
        self._source_connector_factory = source_connector_factory

    def execute(
        self,
        project_id: str,
        scenario_id: str,
        objective: str,
        inputs: dict[str, object],
        requested_plan_id: str | None = None,
    ) -> RunScenarioResult:
        resolved_scenario_id, deprecated_alias_used = resolve_scenario_id(scenario_id)
        enrichment = enrich_repo_inputs_for_scenario(resolved_scenario_id, inputs, self._source_connector_factory)
        enriched_inputs = enrichment.inputs
        self._catalog.validate_inputs(resolved_scenario_id, enriched_inputs)

        subscription = self._billing_read_model.get_active_subscription(project_id)
        effective_plan_id = subscription.plan_id if subscription else (requested_plan_id or "starter")

        allowed, consumed, limit = self._usage_meter.consume(project_id=project_id, plan_id=effective_plan_id, units=1)
        if not allowed:
            raise ValueError(f"usage_limit_exceeded plan={effective_plan_id} consumed={consumed} limit={limit}")

        key = build_idempotency_key(project_id, resolved_scenario_id, objective)
        before_ids = {e.id for e in self._executions.list_recent(200) if e.idempotency_key == key}
        execution = self._start_execution.execute(
            project_id=project_id,
            scenario_id=resolved_scenario_id,
            objective=objective,
            agent="dev_architect",
        )
        self._audit.append(build_event(execution.id, "scenario_repo_enrichment", to_audit_payload(enrichment)))
        self._audit.append(build_event(execution.id, "scenario_inputs", json.dumps(enriched_inputs, sort_keys=True)))
        if deprecated_alias_used:
            self._audit.append(
                build_event(
                    execution.id,
                    "scenario_alias_deprecated",
                    f"legacy_id={scenario_id} resolved_to={resolved_scenario_id}",
                )
            )
        reused = execution.id in before_ids
        return RunScenarioResult(
            execution_id=execution.id,
            status=execution.status,
            reused=reused,
            scenario_id=resolved_scenario_id,
            deprecated_alias_used=deprecated_alias_used,
            usage=UsageSnapshot(
                plan_id=effective_plan_id,
                daily_limit=limit,
                consumed_today=consumed,
                remaining_today=max(0, limit - consumed),
                warning_level=warning_for_ratio(consumed, limit),
            ),
        )
