import { useMemo, useState } from 'react'

import { AuditEvent } from '../../shared/lib/api'

type LogsPageProps = {
  selectedExecutionId: string | null
  events: AuditEvent[]
  isLoading: boolean
  errorMessage: string | null
}

export function LogsPage({ selectedExecutionId, events, isLoading, errorMessage }: LogsPageProps) {
  const [filter, setFilter] = useState('all')

  const filteredEvents = useMemo(() => {
    if (filter === 'all') return events
    return events.filter((event) => event.event_type === filter)
  }, [events, filter])

  if (isLoading) {
    return <p className="text-slate-300">Carregando timeline da execução...</p>
  }

  if (errorMessage) {
    return <p className="text-rose-300">{errorMessage}</p>
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Logs & Audit</h2>
      <p className="mt-2 text-slate-300">Execução selecionada: {selectedExecutionId ?? 'nenhuma'}</p>

      <div className="mt-4">
        <label className="mr-2 text-sm text-slate-300" htmlFor="eventFilter">
          Filtro
        </label>
        <select
          id="eventFilter"
          className="rounded bg-slate-800 px-2 py-1 text-sm"
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
        >
          <option value="all">Todos</option>
          <option value="queued">queued</option>
          <option value="enqueued">enqueued</option>
          <option value="started">started</option>
          <option value="completed">completed</option>
          <option value="failed">failed</option>
        </select>
      </div>

      {filteredEvents.length === 0 ? (
        <p className="mt-4 text-slate-400">Nenhum evento encontrado para o filtro atual.</p>
      ) : (
        <ul className="mt-4 space-y-2">
          {filteredEvents.map((event) => (
            <li key={event.id} className="rounded border border-slate-700 bg-slate-900 p-3">
              <p className="text-xs text-slate-400">{new Date(event.created_at).toLocaleString()}</p>
              <p className="text-sm text-cyan-300">{event.event_type}</p>
              <p className="text-sm text-slate-200">{event.message}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
