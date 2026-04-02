import { BillingAdminOverview, BillingInvoiceHistoryEntry, BillingUsageHistoryItem } from '../../shared/lib/api'

type BillingPageProps = {
  projectId: string
  overview: BillingAdminOverview | null
  invoices: BillingInvoiceHistoryEntry[]
  usageItems: BillingUsageHistoryItem[]
  isLoading: boolean
  errorMessage: string | null
}

export function BillingPage({ projectId, overview, invoices, usageItems, isLoading, errorMessage }: BillingPageProps) {
  if (isLoading) {
    return <p className="text-slate-300">Carregando painel comercial de billing...</p>
  }

  if (errorMessage) {
    return <p className="text-rose-300">{errorMessage}</p>
  }

  return (
    <section className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">Billing admin overview</h1>
        <p className="text-sm text-slate-300">Projeto: {projectId}</p>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        <article className="rounded border border-slate-800 bg-slate-900 p-4">
          <h2 className="text-sm font-medium text-slate-300">Última scheduler run</h2>
          <p className="mt-2 text-lg text-white">
            {overview?.latest_scheduler_run ? (overview.latest_scheduler_run.success ? 'Sucesso' : 'Falha') : 'Sem runs'}
          </p>
          <p className="text-xs text-slate-400">
            attempts: {overview?.latest_scheduler_run?.attempts ?? 0} · alerts: {overview?.recent_alerts.length ?? 0}
          </p>
        </article>
        <article className="rounded border border-slate-800 bg-slate-900 p-4">
          <h2 className="text-sm font-medium text-slate-300">Invoices no histórico</h2>
          <p className="mt-2 text-lg text-white">{invoices.length}</p>
        </article>
        <article className="rounded border border-slate-800 bg-slate-900 p-4">
          <h2 className="text-sm font-medium text-slate-300">Uso no período</h2>
          <p className="mt-2 text-lg text-white">{usageItems.reduce((total, item) => total + item.units, 0)} units</p>
        </article>
      </div>

      <div className="rounded border border-slate-800 bg-slate-900 p-4">
        <h2 className="mb-3 text-lg font-medium text-white">Invoices (history)</h2>
        <ul className="space-y-2 text-sm">
          {invoices.slice(0, 8).map((invoice) => (
            <li key={invoice.id} className="rounded border border-slate-800 p-2 text-slate-200">
              <p>
                {invoice.id} · {invoice.status} · ${(invoice.total_cents / 100).toFixed(2)}
              </p>
              <p className="text-xs text-slate-400">
                items: {invoice.item_count} · transitions: {invoice.transitions.length}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
