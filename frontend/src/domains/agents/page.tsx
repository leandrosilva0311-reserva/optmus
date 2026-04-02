import { AgentCatalogItem } from '../../shared/lib/api'

type AgentsPageProps = {
  agents: AgentCatalogItem[]
  isLoading: boolean
  errorMessage: string | null
}

export function AgentsPage({ agents, isLoading, errorMessage }: AgentsPageProps) {
  if (isLoading) return <p className="text-slate-300">Carregando catálogo de agentes...</p>
  if (errorMessage) return <p className="text-rose-300">{errorMessage}</p>
  if (agents.length === 0) return <p className="text-slate-400">Nenhum agente disponível.</p>

  return (
    <section>
      <h2 className="text-2xl font-semibold">Catálogo de Agentes</h2>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {agents.map((agent) => (
          <article key={agent.key} className="rounded border border-slate-700 bg-slate-900 p-4">
            <h3 className="font-semibold text-cyan-300">{agent.title}</h3>
            <ul className="mt-2 list-disc pl-5 text-sm text-slate-300">
              {agent.responsibilities.map((responsibility) => (
                <li key={responsibility}>{responsibility}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  )
}
