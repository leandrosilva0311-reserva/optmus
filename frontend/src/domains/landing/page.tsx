export function LandingPage() {
  return (
    <section className="grid gap-8 py-10 md:grid-cols-2">
      <div>
        <p className="text-cyan-300">Agentic Engineering Platform</p>
        <h1 className="mt-2 text-4xl font-bold text-white">Operação de agentes com segurança e auditabilidade.</h1>
        <p className="mt-3 text-slate-300">
          Núcleo modular para agentes de engenharia, QA, operações e análise com execução rastreável e pronto para
          expansão multi-tenant.
        </p>
        <div className="mt-6 flex gap-3">
          <button className="rounded bg-cyan-600 px-4 py-2 font-semibold">Começar agora</button>
          <button className="rounded border border-slate-600 px-4 py-2">Ver documentação</button>
        </div>
      </div>
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-6">
        <h3 className="text-lg font-semibold">Recursos da fase 2</h3>
        <ul className="mt-3 space-y-2 text-sm text-slate-300">
          <li>• Execuções persistidas em PostgreSQL</li>
          <li>• Sessão em Redis e proteção de rotas</li>
          <li>• Job queue assíncrona com ARQ</li>
          <li>• Timeline de auditoria por execução</li>
        </ul>
      </div>
    </section>
  )
}
