import { Execution, Subtask } from '../../shared/lib/api'

type WorkspacePageProps = {
  executions: Execution[]
  subtasks: Subtask[]
  onSelectExecution: (id: string) => void
  isLoading: boolean
  errorMessage: string | null
}

export function WorkspacePage({ executions, subtasks, onSelectExecution, isLoading, errorMessage }: WorkspacePageProps) {
  if (isLoading) {
    return <p className="text-slate-300">Carregando execuções...</p>
  }

  if (errorMessage) {
    return <p className="text-rose-300">{errorMessage}</p>
  }

  if (executions.length === 0) {
    return <p className="text-slate-400">Ainda não existem execuções para exibir.</p>
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Workspace</h2>
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
                    Ver execução
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-6">
        <h3 className="text-lg font-semibold">Subtarefas da execução selecionada</h3>
        {subtasks.length === 0 ? (
          <p className="mt-2 text-slate-400">Selecione uma execução para carregar subtarefas.</p>
        ) : (
          <ul className="mt-2 space-y-2 text-sm">
            {subtasks.map((subtask) => (
              <li key={subtask.id} className="rounded border border-slate-700 bg-slate-900 p-3">
                <p className="text-cyan-300">{subtask.agent}</p>
                <p>{subtask.title}</p>
                <p className="text-slate-400">depends_on: {subtask.depends_on.join(', ') || 'none'}</p>
                <p className="text-slate-400">status: {subtask.status}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
