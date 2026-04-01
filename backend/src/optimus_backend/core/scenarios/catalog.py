from optimus_backend.core.scenarios.models import ScenarioDefinition, ScenarioDefinitionOfDone, ScenarioInputField

SCENARIO_PARTIAL_STATES: tuple[str, ...] = (
    "partial_success",
    "external_dependency_unavailable",
    "manual_validation_required",
)


class ScenarioCatalog:
    def __init__(self) -> None:
        self._items: dict[str, ScenarioDefinition] = {
            "public_api_health": ScenarioDefinition(
                scenario_id="public_api_health",
                name="Public API health triage",
                required_inputs=(
                    ScenarioInputField("request_id", "ID da requisição originadora"),
                    ScenarioInputField("execution_id", "ID da execução de investigação"),
                    ScenarioInputField("order_id", "ID transacional/correlação"),
                    ScenarioInputField("restaurant_id", "ID da unidade/tenant afetada"),
                    ScenarioInputField("time_window_start", "Início da janela ISO-8601"),
                    ScenarioInputField("time_window_end", "Fim da janela ISO-8601"),
                ),
                done=ScenarioDefinitionOfDone(
                    success_criteria=(
                        "Correlações em logs retornam trilha request→order→tenant sem lacunas.",
                        "Fila analisada com backlog, oldest age, failed count e latência estimada.",
                        "Relatório final inclui bloco de negócio e ação imediata atribuível.",
                    ),
                    failure_criteria=(
                        "Sem dados suficientes para correlação por ausência de chaves obrigatórias.",
                        "Dependência externa indisponível para consulta de filas ou logs.",
                        "Sem proposta de ação imediata com responsável sugerido.",
                    ),
                ),
                supported_terminal_states=SCENARIO_PARTIAL_STATES,
                business_value="Detecta regressões de disponibilidade antes de impacto massivo em clientes.",
                recommended_for=("SaaS API-first", "Times de SRE/Ops", "On-call"),
                estimated_runtime_minutes=4,
                onboarding_steps=(
                    "Conectar fonte de logs por request_id",
                    "Configurar inspeção de fila",
                    "Validar playbook de resposta",
                ),
            ),
            "checkout_flow_validation": ScenarioDefinition(
                scenario_id="checkout_flow_validation",
                name="Checkout flow consistency check",
                required_inputs=(
                    ScenarioInputField("request_id", "ID da requisição originadora"),
                    ScenarioInputField("execution_id", "ID da execução de investigação"),
                    ScenarioInputField("order_id", "ID da transação/pedido com divergência"),
                    ScenarioInputField("restaurant_id", "ID da unidade/tenant afetada"),
                    ScenarioInputField("time_window_start", "Início da janela ISO-8601"),
                    ScenarioInputField("time_window_end", "Fim da janela ISO-8601"),
                ),
                done=ScenarioDefinitionOfDone(
                    success_criteria=(
                        "Estados entre componentes do checkout reconciliados ou divergência classificada.",
                        "Dependências externas mapeadas com status de disponibilidade.",
                        "Resultado classificado em sucesso, parcial ou validação manual necessária.",
                    ),
                    failure_criteria=(
                        "Não foi possível verificar estado por indisponibilidade externa.",
                        "Sem rastreabilidade por request_id/execution_id/order_id/restaurant_id.",
                        "Sem classificação final do caso para operação.",
                    ),
                ),
                supported_terminal_states=SCENARIO_PARTIAL_STATES,
                business_value="Reduz perdas de conversão em fluxos de pagamento e confirmação de pedidos.",
                recommended_for=("E-commerce", "Marketplaces", "Plataformas transacionais"),
                estimated_runtime_minutes=6,
                onboarding_steps=(
                    "Mapear eventos de checkout no observability stack",
                    "Habilitar correlação de ordem e pagamento",
                    "Definir owner de resposta para falhas",
                ),
            ),
            "queue_health": ScenarioDefinition(
                scenario_id="queue_health",
                name="Queue health and latency diagnosis",
                required_inputs=(
                    ScenarioInputField("request_id", "ID da requisição originadora"),
                    ScenarioInputField("execution_id", "ID da execução de investigação"),
                    ScenarioInputField("restaurant_id", "ID da unidade/tenant afetada"),
                    ScenarioInputField("time_window_start", "Início da janela ISO-8601"),
                    ScenarioInputField("time_window_end", "Fim da janela ISO-8601"),
                ),
                done=ScenarioDefinitionOfDone(
                    success_criteria=(
                        "Backlog e idade da fila quantificados com latência estimada.",
                        "Causa operacional principal classificada por severidade.",
                        "Ação imediata com responsável sugerido no bloco final.",
                    ),
                    failure_criteria=(
                        "Métricas obrigatórias da fila ausentes no diagnóstico.",
                        "Dependência externa de inspeção indisponível.",
                        "Sem classificação de severidade e owner recomendado.",
                    ),
                ),
                supported_terminal_states=SCENARIO_PARTIAL_STATES,
                business_value="Evita incidentes por acúmulo de backlog e degradação progressiva de throughput.",
                recommended_for=("Backoffice", "Processamento assíncrono", "Times de plataforma"),
                estimated_runtime_minutes=3,
                onboarding_steps=(
                    "Configurar integração de fila principal",
                    "Definir limiares de backlog/latência",
                    "Conectar alertas operacionais",
                ),
            ),
            "incident_timeline_reconstruction": ScenarioDefinition(
                scenario_id="incident_timeline_reconstruction",
                name="Incident timeline reconstruction",
                required_inputs=(
                    ScenarioInputField("request_id", "ID da requisição ou trigger do incidente"),
                    ScenarioInputField("execution_id", "ID da execução de investigação"),
                    ScenarioInputField("restaurant_id", "ID da unidade/tenant afetada"),
                    ScenarioInputField("time_window_start", "Início da janela ISO-8601"),
                    ScenarioInputField("time_window_end", "Fim da janela ISO-8601"),
                ),
                done=ScenarioDefinitionOfDone(
                    success_criteria=(
                        "Linha do tempo consolidada com eventos críticos ordenados.",
                        "Causa provável e impactos mapeados por janela temporal.",
                        "Plano imediato de contenção com owner definido.",
                    ),
                    failure_criteria=(
                        "Eventos insuficientes para reconstrução cronológica confiável.",
                        "Dependência de logs indisponível para período do incidente.",
                        "Sem recomendação acionável de contenção.",
                    ),
                ),
                supported_terminal_states=SCENARIO_PARTIAL_STATES,
                business_value="Acelera postmortem e redução de MTTR com narrativa técnica auditável.",
                recommended_for=("Incident response", "SRE", "Suporte técnico"),
                estimated_runtime_minutes=7,
                onboarding_steps=(
                    "Configurar retenção mínima de logs",
                    "Padronizar chaves de correlação",
                    "Definir template de postmortem",
                ),
            ),
        }
        self._aliases: dict[str, str] = {
            "kaiso_whatsapp_incident": "public_api_health",
            "kaiso_kds_pos_sync": "checkout_flow_validation",
        }

    def _resolve(self, scenario_id: str) -> str:
        return self._aliases.get(scenario_id, scenario_id)

    def get(self, scenario_id: str) -> ScenarioDefinition:
        resolved_id = self._resolve(scenario_id)
        scenario = self._items.get(resolved_id)
        if scenario is None:
            raise KeyError(f"scenario '{scenario_id}' not found")
        return scenario

    def list_all(self) -> list[ScenarioDefinition]:
        return list(self._items.values())

    def validate_inputs(self, scenario_id: str, payload: dict[str, str]) -> None:
        scenario = self.get(scenario_id)
        missing = [field.name for field in scenario.required_inputs if not payload.get(field.name)]
        if missing:
            raise ValueError(f"missing required scenario inputs: {', '.join(missing)}")
