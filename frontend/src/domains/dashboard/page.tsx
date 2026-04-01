import { Execution } from '../../shared/lib/api'

type DashboardPageProps = {
  executions: Execution[]
  isLoading: boolean
  errorMessage: string | null
}

export function DashboardPage({ executions, isLoading, errorMessage }: DashboardPageProps) {
  if (isLoading) {
    return <p className="text-slate-300">Carregando métricas operacionais...</p>
  }

  if (errorMessage) {
    return <p className="text-rose-300">{errorMessage}</p>
  }

  if (executions.length === 0) {
    return <p className="text-slate-400">Nenhuma execução encontrada para o workspace atual.</p>
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Dashboard Operacional</h2>
      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <Card label="Execuções" value={String(executions.length)} />
        <Card label="Concluídas" value={String(executions.filter((e) => e.status === 'completed').length)} />
        <Card label="Falhas" value={String(executions.filter((e) => e.status === 'failed').length)} />
        <Card label="Último agente" value={executions[0]?.agent ?? '-'} />
      </div>
    </section>
  )
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </article>
  )
}
