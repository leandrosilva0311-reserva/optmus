from optimus_backend.core.scenarios.models import ScenarioDefinition, ScenarioDefinitionOfDone, ScenarioInputField

SCENARIO_PARTIAL_STATES: tuple[str, ...] = (
    "partial_success",
    "external_dependency_unavailable",
    "manual_validation_required",
)


class ScenarioCatalog:
    def __init__(self) -> None:
        self._items: dict[str, ScenarioDefinition] = {
            "kaiso_whatsapp_incident": ScenarioDefinition(
                scenario_id="kaiso_whatsapp_incident",
                name="Kaiso WhatsApp incident triage",
                required_inputs=(
                    ScenarioInputField("request_id", "ID da requisição originadora"),
                    ScenarioInputField("execution_id", "ID da execução de investigação"),
                    ScenarioInputField("order_id", "ID do pedido no domínio Kaiso"),
                    ScenarioInputField("restaurant_id", "ID do restaurante afetado"),
                    ScenarioInputField("time_window_start", "Início da janela ISO-8601"),
                    ScenarioInputField("time_window_end", "Fim da janela ISO-8601"),
                ),
                done=ScenarioDefinitionOfDone(
                    success_criteria=(
                        "Correlações em logs retornam trilha request→order→restaurant sem lacunas.",
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
            ),
            "kaiso_kds_pos_sync": ScenarioDefinition(
                scenario_id="kaiso_kds_pos_sync",
                name="Kaiso KDS/POS consistency check",
                required_inputs=(
                    ScenarioInputField("request_id", "ID da requisição originadora"),
                    ScenarioInputField("execution_id", "ID da execução de investigação"),
                    ScenarioInputField("order_id", "ID do pedido com divergência"),
                    ScenarioInputField("restaurant_id", "ID do restaurante afetado"),
                    ScenarioInputField("time_window_start", "Início da janela ISO-8601"),
                    ScenarioInputField("time_window_end", "Fim da janela ISO-8601"),
                ),
                done=ScenarioDefinitionOfDone(
                    success_criteria=(
                        "Estados entre KDS e POS reconciliados ou divergência classificada.",
                        "Dependências externas mapeadas com status de disponibilidade.",
                        "Resultado classificado em sucesso, parcial ou validação manual necessária.",
                    ),
                    failure_criteria=(
                        "Não foi possível verificar estado em KDS/POS por indisponibilidade externa.",
                        "Sem rastreabilidade por request_id/execution_id/order_id/restaurant_id.",
                        "Sem classificação final do caso para operação.",
                    ),
                ),
                supported_terminal_states=SCENARIO_PARTIAL_STATES,
            ),
        }

    def get(self, scenario_id: str) -> ScenarioDefinition:
        scenario = self._items.get(scenario_id)
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
