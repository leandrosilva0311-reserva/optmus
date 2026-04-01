import { Execution, ScenarioCatalogItem, ScenarioDetail, Subtask } from '../../shared/lib/api'

type WorkspacePageProps = {
  executions: Execution[]
  subtasks: Subtask[]
  scenarioDetail: ScenarioDetail | null
  scenarioCatalog: ScenarioCatalogItem[]
  selectedScenarioId: string
  scenarioObjective: string
  scenarioInputs: Record<string, string>
  onChangeScenarioId: (id: string) => void
  onChangeScenarioObjective: (value: string) => void
  onChangeScenarioInput: (field: string, value: string) => void
  selectedPlanId: string
  usageHint: string | null
  onChangePlanId: (planId: string) => void
  onSelectExecution: (id: string) => void
  onRunScenario: () => void
  isLoading: boolean
  errorMessage: string | null
}

export function WorkspacePage({
  executions,
  subtasks,
  scenarioDetail,
  scenarioCatalog,
  selectedScenarioId,
  scenarioObjective,
  scenarioInputs,
  onChangeScenarioId,
  onChangeScenarioObjective,
  onChangeScenarioInput,
  selectedPlanId,
  usageHint,
  onChangePlanId,
  onSelectExecution,
  onRunScenario,
  isLoading,
  errorMessage,
}: WorkspacePageProps) {
  if (isLoading) return <p className="text-slate-300">Carregando execuções...</p>
  if (errorMessage) return <p className="text-rose-300">{errorMessage}</p>

  const selectedScenario = scenarioCatalog.find((item) => item.scenario_id === selectedScenarioId) ?? null

  return (
    <section>
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Workspace</h2>
      </div>

      <div className="mt-4 rounded border border-slate-700 bg-slate-900 p-4">
        <h3 className="text-lg font-semibold">Executar cenário operacional</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <label className="text-sm">
            Cenário
            <select
              className="mt-1 w-full rounded bg-slate-800 px-2 py-2"
              value={selectedScenarioId}
              onChange={(event) => onChangeScenarioId(event.target.value)}
            >
              {scenarioCatalog.map((scenario) => (
                <option key={scenario.scenario_id} value={scenario.scenario_id}>
                  {scenario.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Objetivo
            <input
              className="mt-1 w-full rounded bg-slate-800 px-2 py-2"
              value={scenarioObjective}
              onChange={(event) => onChangeScenarioObjective(event.target.value)}
              placeholder="Descreva o objetivo da execução"
            />
          </label>
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <label className="text-sm">
            Plano
            <select className="mt-1 w-full rounded bg-slate-800 px-2 py-2" value={selectedPlanId} onChange={(event) => onChangePlanId(event.target.value)}>
              <option value="starter">starter</option>
              <option value="growth">growth</option>
              <option value="enterprise">enterprise</option>
            </select>
          </label>
          {selectedScenario ? (
            <div className="rounded bg-slate-800 p-3 text-xs space-y-1">
              <p>valor de negócio: {selectedScenario.business_value}</p>
              <p>tempo estimado: {selectedScenario.estimated_runtime_minutes} min</p>
              <p>indicado para: {selectedScenario.recommended_for.join(', ')}</p>
            </div>
          ) : null}
        </div>
        {selectedScenario ? (
          <div className="mt-2 rounded bg-slate-800 p-3 text-xs">
            onboarding: {selectedScenario.onboarding_steps.join(' • ')}
          </div>
        ) : null}
        {selectedScenario ? (
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {selectedScenario.required_inputs.map((field) => (
              <label key={field} className="text-sm">
                {field}
                <input
                  className="mt-1 w-full rounded bg-slate-800 px-2 py-2"
                  value={scenarioInputs[field] ?? ''}
                  onChange={(event) => onChangeScenarioInput(field, event.target.value)}
                />
              </label>
            ))}
          </div>
        ) : null}

        <button className="mt-4 rounded bg-cyan-600 px-3 py-2 text-sm" onClick={onRunScenario}>
          Executar cenário
        </button>
        {usageHint ? <p className="mt-2 text-xs text-cyan-300">{usageHint}</p> : null}
      </div>

      {executions.length === 0 ? (
        <p className="mt-4 text-slate-400">Ainda não existem execuções para exibir.</p>
      ) : (
        <div className="mt-4 overflow-hidden rounded-lg border border-slate-700">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900 text-slate-300">
              <tr>
                <th className="p-3">Status</th>
                <th className="p-3">Agente</th>
                <th className="p-3">Objetivo</th>
                <th className="p-3">Duração</th>
                <th className="p-3">Ação</th>
              </tr>
            </thead>
            <tbody>
              {executions.map((execution) => (
                <tr key={execution.id} className="border-t border-slate-800">
                  <td className="p-3">{execution.status}</td>
                  <td className="p-3">{execution.agent}</td>
                  <td className="p-3">{execution.objective}</td>
                  <td className="p-3">{execution.duration_ms ?? '-'} ms</td>
                  <td className="p-3">
                    <button className="text-cyan-300" onClick={() => onSelectExecution(execution.id)}>
                      Abrir execução
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div>
          <h3 className="text-lg font-semibold">Subtarefas</h3>
          {subtasks.length === 0 ? (
            <p className="mt-2 text-slate-400">Selecione uma execução para carregar subtarefas.</p>
          ) : (
            <ul className="mt-2 space-y-2 text-sm">
              {subtasks.map((subtask) => (
                <li key={subtask.id} className="rounded border border-slate-700 bg-slate-900 p-3">
                  <p className="text-cyan-300">{subtask.agent}</p>
                  <p>{subtask.title}</p>
                  <p className="text-slate-400">handoff: {subtask.handoff_reason ?? 'n/a'}</p>
                  <p className="text-slate-400">attempt: {subtask.attempt ?? 1}</p>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h3 className="text-lg font-semibold">Resultado e bloco final de negócio</h3>
          {!scenarioDetail ? (
            <p className="mt-2 text-slate-400">Selecione uma execução para ver resultado completo.</p>
          ) : (
            <div className="mt-2 rounded border border-slate-700 bg-slate-900 p-3 text-sm space-y-2">
              <p>status: {scenarioDetail.status}</p>
              <p>
                budget: steps={scenarioDetail.max_steps}, tools={scenarioDetail.max_tool_calls}, duration=
                {scenarioDetail.max_duration_ms}ms
              </p>
              <p>summary: {scenarioDetail.summary ?? 'n/a'}</p>
              {scenarioDetail.final_business_block ? (
                <div className="rounded bg-slate-800 p-3 space-y-1">
                  <p>impacto operacional: {scenarioDetail.final_business_block.operational_impact}</p>
                  <p>impacto comercial: {scenarioDetail.final_business_block.commercial_impact}</p>
                  <p>severidade: {scenarioDetail.final_business_block.severity}</p>
                  <p>ação imediata: {scenarioDetail.final_business_block.immediate_action}</p>
                  <p>responsável sugerido: {scenarioDetail.final_business_block.suggested_owner}</p>
                </div>
              ) : (
                <p className="text-slate-400">Bloco final ainda não disponível.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
