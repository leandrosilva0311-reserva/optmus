from optimus_backend.core.scenarios.models import ScenarioDefinition, ScenarioDefinitionOfDone, ScenarioInputField

SCENARIO_PARTIAL_STATES: tuple[str, ...] = (
    "partial_success",
    "external_dependency_unavailable",
    "manual_validation_required",
)


class ScenarioCatalog:
    def __init__(self) -> None:
        self._items: dict[str, ScenarioDefinition] = {
            "code_analysis": ScenarioDefinition(
                scenario_id="code_analysis",
                name="Code analysis and architecture signals",
                required_inputs=(
                    ScenarioInputField("stack", "Stack/linguagem principal do código analisado"),
                    ScenarioInputField("objective", "Objetivo técnico da análise"),
                    ScenarioInputField("files", "Lista de arquivos [{path, content}] para análise"),
                ),
                done=ScenarioDefinitionOfDone(
                    success_criteria=(
                        "Diagnóstico técnico coerente com evidências de código.",
                        "Recomendações acionáveis com risco e urgência.",
                        "Plano de execução estruturado por passos.",
                    ),
                    failure_criteria=(
                        "Arquivos insuficientes para análise consistente.",
                        "Objetivo da análise ambíguo ou ausente.",
                        "Saída sem evidências rastreáveis.",
                    ),
                ),
                supported_terminal_states=SCENARIO_PARTIAL_STATES,
                business_value="Acelera entendimento de base de código e priorização técnica.",
                recommended_for=("Plataformas SaaS", "Times de engenharia", "Consultoria técnica"),
                estimated_runtime_minutes=6,
                onboarding_steps=(
                    "Fornecer arquivos centrais",
                    "Informar stack e objetivo",
                    "Validar ações sugeridas",
                ),
            ),
            "bug_diagnosis": ScenarioDefinition(
                scenario_id="bug_diagnosis",
                name="Bug diagnosis with technical evidence",
                required_inputs=(
                    ScenarioInputField("observed_error", "Erro observado (stacktrace, mensagem, sintoma)"),
                    ScenarioInputField("stack", "Stack/linguagem do sistema"),
                    ScenarioInputField("objective", "Objetivo da investigação"),
                    ScenarioInputField("source_text", "Trecho de código/contexto mínimo para diagnóstico"),
                ),
                done=ScenarioDefinitionOfDone(
                    success_criteria=(
                        "Causa-raiz provável descrita com evidências.",
                        "Recomendações de correção priorizadas.",
                        "Plano de execução com validações objetivas.",
                    ),
                    failure_criteria=(
                        "Sem erro observado suficiente para hipóteses úteis.",
                        "Sem vínculo entre diagnóstico e evidências.",
                        "Plano de execução incompleto.",
                    ),
                ),
                supported_terminal_states=SCENARIO_PARTIAL_STATES,
                business_value="Reduz tempo de triagem e aumenta precisão de correção de bugs.",
                recommended_for=("Times backend", "SRE", "Plataformas transacionais"),
                estimated_runtime_minutes=7,
                onboarding_steps=(
                    "Enviar erro observado",
                    "Anexar contexto de código",
                    "Definir objetivo de correção",
                ),
            ),
            "refactor_suggestion": ScenarioDefinition(
                scenario_id="refactor_suggestion",
                name="Refactor suggestion and risk analysis",
                required_inputs=(
                    ScenarioInputField("stack", "Stack principal"),
                    ScenarioInputField("objective", "Objetivo de refatoração"),
                    ScenarioInputField("files", "Arquivos de referência [{path, content}]"),
                    ScenarioInputField("additional_instructions", "Restrições ou contexto extra"),
                ),
                done=ScenarioDefinitionOfDone(
                    success_criteria=(
                        "Sugestão de refatoração alinhada ao objetivo.",
                        "Riscos e trade-offs explícitos.",
                        "Plano incremental com checkpoints.",
                    ),
                    failure_criteria=(
                        "Sem clareza de objetivo/restrições.",
                        "Sugestões sem impacto técnico verificável.",
                        "Ausência de plano incremental.",
                    ),
                ),
                supported_terminal_states=SCENARIO_PARTIAL_STATES,
                business_value="Melhora manutenção e reduz acoplamento de forma controlada.",
                recommended_for=("Times de plataforma", "Arquitetura", "Modernização"),
                estimated_runtime_minutes=8,
                onboarding_steps=(
                    "Definir objetivo de refatoração",
                    "Anexar arquivos relevantes",
                    "Informar restrições",
                ),
            ),
            "patch_review": ScenarioDefinition(
                scenario_id="patch_review",
                name="Patch review with structured risk output",
                required_inputs=(
                    ScenarioInputField("diff_text", "Diff textual obrigatório do patch"),
                    ScenarioInputField("objective", "Objetivo da revisão"),
                    ScenarioInputField("stack", "Stack do projeto"),
                ),
                done=ScenarioDefinitionOfDone(
                    success_criteria=(
                        "Diagnóstico do patch com evidências de diff.",
                        "Riscos e urgência explícitos.",
                        "Plano de execução com etapas verificáveis.",
                    ),
                    failure_criteria=(
                        "Diff ausente ou inválido.",
                        "Sem recomendações acionáveis.",
                        "Sem plano de validação pós-patch.",
                    ),
                ),
                supported_terminal_states=SCENARIO_PARTIAL_STATES,
                business_value="Aumenta qualidade de revisão técnica e reduz regressões em produção.",
                recommended_for=("Code review", "QA", "Tech lead"),
                estimated_runtime_minutes=5,
                onboarding_steps=(
                    "Enviar diff completo",
                    "Informar objetivo da mudança",
                    "Executar plano sugerido",
                ),
            ),
        }

    def get(self, scenario_id: str) -> ScenarioDefinition:
        scenario = self._items.get(scenario_id)
        if scenario is None:
            raise KeyError(f"scenario '{scenario_id}' not found")
        return scenario

    def list_all(self) -> list[ScenarioDefinition]:
        return list(self._items.values())

    def _validate_files(self, files_value: object) -> None:
        if not isinstance(files_value, list) or not files_value:
            raise ValueError("files must be a non-empty list of {path, content}")
        for item in files_value:
            if not isinstance(item, dict):
                raise ValueError("each file item must be an object with path and content")
            path = str(item.get("path", "")).strip()
            content = str(item.get("content", "")).strip()
            if not path or not content:
                raise ValueError("each file item must contain non-empty path and content")

    def validate_inputs(self, scenario_id: str, payload: dict[str, object]) -> None:
        scenario = self.get(scenario_id)
        missing = [field.name for field in scenario.required_inputs if payload.get(field.name) in (None, "", [])]
        if missing:
            raise ValueError(f"missing required scenario inputs: {', '.join(missing)}")

        if "files" in {f.name for f in scenario.required_inputs}:
            self._validate_files(payload.get("files"))

        if scenario_id == "patch_review" and not str(payload.get("diff_text", "")).strip():
            raise ValueError("diff_text is required for patch_review")
