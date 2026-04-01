import { Execution, ScenarioDetail, Subtask } from '../../shared/lib/api'

type WorkspacePageProps = {
  executions: Execution[]
  subtasks: Subtask[]
  scenarioDetail: ScenarioDetail | null
  onSelectExecution: (id: string) => void
  onRunScenario: () => void
  isLoading: boolean
  errorMessage: string | null
}

export function WorkspacePage({
  executions,
  subtasks,
  scenarioDetail,
  onSelectExecution,
  onRunScenario,
  isLoading,
  errorMessage,
}: WorkspacePageProps) {
  if (isLoading) return <p className="text-slate-300">Carregando execuções...</p>
  if (errorMessage) return <p className="text-rose-300">{errorMessage}</p>

  return (
    <section>
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Workspace</h2>
        <button className="rounded bg-cyan-600 px-3 py-2 text-sm" onClick={onRunScenario}>
          Run health_check scenario
        </button>
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
                  <p className="text-slate-400">attempt: {subtask.attempt}</p>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h3 className="text-lg font-semibold">Plano e decisão operacional</h3>
          {!scenarioDetail ? (
            <p className="mt-2 text-slate-400">Selecione uma execução para ver orçamento e decisão.</p>
          ) : (
            <div className="mt-2 rounded border border-slate-700 bg-slate-900 p-3 text-sm">
              <p>status: {scenarioDetail.status}</p>
              <p>budget: steps={scenarioDetail.max_steps}, tools={scenarioDetail.max_tool_calls}, duration={scenarioDetail.max_duration_ms}ms</p>
              <p className="mt-2 text-slate-300">next action: validar timeline e aplicar passo prioritário do AnalystAgent.</p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
