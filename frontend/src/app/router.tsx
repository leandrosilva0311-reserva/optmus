import { useEffect, useState } from 'react'

import { LoginForm } from '../domains/auth/components/login-form'
import { AgentsPage } from '../domains/agents/page'
import { DashboardPage } from '../domains/dashboard/page'
import { LandingPage } from '../domains/landing/page'
import { LogsPage } from '../domains/logs/page'
import { WorkspacePage } from '../domains/workspace/page'
import { BillingPage } from '../domains/billing/page'
import { TopNav } from '../shared/components/top-nav'
import {
  AgentCatalogItem,
  AuditEvent,
  BillingAdminOverview,
  BillingInvoiceHistoryEntry,
  BillingUsageHistoryItem,
  Execution,
  ScenarioCatalogItem,
  ScenarioDetail,
  Subtask,
  getAgentCatalog,
  getBillingAdminOverview,
  getBillingInvoiceHistory,
  getBillingUsagePeriod,
  getScenarioDetail,
  getScenarioTimeline,
  getSubtasks,
  getTimeline,
  listExecutions,
  listScenarioCatalog,
  login,
  logout,
  runScenario,
} from '../shared/lib/api'

export function AppRouter() {
  const [section, setSection] = useState('landing')
  const [sessionId, setSessionId] = useState<string | null>(localStorage.getItem('session_id'))
  const [role, setRole] = useState<string | null>(localStorage.getItem('role'))
  const [executions, setExecutions] = useState<Execution[]>([])
  const [subtasks, setSubtasks] = useState<Subtask[]>([])
  const [agents, setAgents] = useState<AgentCatalogItem[]>([])
  const [scenarioCatalog, setScenarioCatalog] = useState<ScenarioCatalogItem[]>([])
  const [scenarioDetail, setScenarioDetail] = useState<ScenarioDetail | null>(null)
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null)
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [selectedScenarioId, setSelectedScenarioId] = useState('public_api_health')
  const [scenarioObjective, setScenarioObjective] = useState('Validar saúde operacional da API pública')
  const [scenarioInputs, setScenarioInputs] = useState<Record<string, string>>({})
  const [selectedPlanId, setSelectedPlanId] = useState('starter')
  const [usageHint, setUsageHint] = useState<string | null>(null)
  const [loadingExecutions, setLoadingExecutions] = useState(false)
  const [executionsError, setExecutionsError] = useState<string | null>(null)
  const [loadingTimeline, setLoadingTimeline] = useState(false)
  const [timelineError, setTimelineError] = useState<string | null>(null)
  const [loadingAgents, setLoadingAgents] = useState(false)
  const [agentsError, setAgentsError] = useState<string | null>(null)
  const [billingOverview, setBillingOverview] = useState<BillingAdminOverview | null>(null)
  const [billingInvoices, setBillingInvoices] = useState<BillingInvoiceHistoryEntry[]>([])
  const [billingUsageItems, setBillingUsageItems] = useState<BillingUsageHistoryItem[]>([])
  const [loadingBilling, setLoadingBilling] = useState(false)
  const [billingError, setBillingError] = useState<string | null>(null)
  const billingProjectId = 'default'

  useEffect(() => {
    if (!sessionId) return

    async function loadBootData() {
      setLoadingExecutions(true)
      setLoadingAgents(true)
      setExecutionsError(null)
      setAgentsError(null)

      try {
        const [execData, agentData, scenarios] = await Promise.all([
          listExecutions(sessionId),
          getAgentCatalog(sessionId),
          listScenarioCatalog(sessionId),
        ])
        setExecutions(execData)
        setAgents(agentData)
        setScenarioCatalog(scenarios)
        if (scenarios.length > 0) {
          setSelectedScenarioId(scenarios[0].scenario_id)
        }
      } catch {
        setExecutionsError('Não foi possível carregar execuções.')
        setAgentsError('Não foi possível carregar catálogo de agentes.')
      } finally {
        setLoadingExecutions(false)
        setLoadingAgents(false)
      }
    }

    loadBootData()
  }, [sessionId])

  useEffect(() => {
    if (!sessionId || section !== 'billing') return
    async function loadBilling() {
      setLoadingBilling(true)
      setBillingError(null)
      try {
        const now = new Date()
        const start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        const [overview, invoices, usage] = await Promise.all([
          getBillingAdminOverview(sessionId),
          getBillingInvoiceHistory(sessionId, billingProjectId),
          getBillingUsagePeriod(sessionId, billingProjectId, start.toISOString(), now.toISOString()),
        ])
        setBillingOverview(overview)
        setBillingInvoices(invoices)
        setBillingUsageItems(usage.items)
      } catch {
        setBillingError('Falha ao carregar dados comerciais de billing.')
      } finally {
        setLoadingBilling(false)
      }
    }
    loadBilling()
  }, [sessionId, section])

  async function handleLogin(email: string, password: string) {
    const data = await login(email, password)
    localStorage.setItem('session_id', data.session_id)
    localStorage.setItem('role', data.role)
    setRole(data.role)
    setSessionId(data.session_id)
    setSection('dashboard')
  }

  async function handleSelectExecution(executionId: string) {
    setSelectedExecutionId(executionId)
    if (!sessionId) return

    setLoadingTimeline(true)
    setTimelineError(null)
    try {
      const [timeline, subtasksData, detail] = await Promise.all([
        getTimeline(sessionId, executionId),
        getSubtasks(sessionId, executionId),
        getScenarioDetail(sessionId, executionId),
      ])
      setEvents(timeline)
      setSubtasks(subtasksData)
      setScenarioDetail(detail)
      setSection('workspace')
    } catch {
      setTimelineError('Falha ao carregar dados da execução.')
      setEvents([])
      setSubtasks([])
      setScenarioDetail(null)
      setSection('logs')
    } finally {
      setLoadingTimeline(false)
    }
  }

  function handleChangeScenarioInput(field: string, value: string) {
    setScenarioInputs((prev) => ({ ...prev, [field]: value }))
  }

  async function handleRunScenario() {
    if (!sessionId) return
    const scenario = scenarioCatalog.find((item) => item.scenario_id === selectedScenarioId)
    if (!scenario) {
      setExecutionsError('Catálogo de cenários não disponível.')
      return
    }

    const missing = scenario.required_inputs.filter((field) => !(scenarioInputs[field] ?? '').trim())
    if (missing.length > 0) {
      setExecutionsError(`Preencha os inputs obrigatórios: ${missing.join(', ')}`)
      return
    }

    try {
      setExecutionsError(null)
      const result = await runScenario(
        sessionId,
        'default',
        selectedScenarioId,
        scenarioObjective,
        Object.fromEntries(scenario.required_inputs.map((field) => [field, scenarioInputs[field]])),
        selectedPlanId
      )
      setUsageHint(`Plano ${result.usage.plan_id}: ${result.usage.consumed_today}/${result.usage.daily_limit} execuções no dia`)
      const [detail, timeline, execData] = await Promise.all([
        getScenarioDetail(sessionId, result.execution_id),
        getScenarioTimeline(sessionId, result.execution_id),
        listExecutions(sessionId),
      ])
      setExecutions(execData)
      setScenarioDetail(detail)
      setEvents(timeline)
      setSelectedExecutionId(result.execution_id)
      setSection('workspace')
    } catch {
      setExecutionsError('Falha ao iniciar cenário operacional.')
    }
  }

  async function handleLogout() {
    if (sessionId) {
      try {
        await logout(sessionId)
      } catch {
        // ignore remote logout errors
      }
    }
    localStorage.removeItem('session_id')
    localStorage.removeItem('role')
    setSessionId(null)
    setRole(null)
    setExecutions([])
    setSubtasks([])
    setAgents([])
    setScenarioCatalog([])
    setScenarioDetail(null)
    setEvents([])
    setSelectedExecutionId(null)
    setExecutionsError(null)
    setTimelineError(null)
    setAgentsError(null)
    setSection('landing')
  }

  const canAccessPrivate = Boolean(sessionId) && Boolean(role)

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <TopNav section={section} onNavigate={setSection} isAuthenticated={canAccessPrivate} onLogout={handleLogout} />
      <main className="mx-auto max-w-6xl px-6 py-8">
        {!canAccessPrivate && section !== 'landing' ? <LoginForm onLogin={handleLogin} /> : null}
        {section === 'landing' && <LandingPage />}
        {section === 'dashboard' && (
          <DashboardPage executions={executions} isLoading={loadingExecutions} errorMessage={executionsError} />
        )}
        {section === 'workspace' && (
          <WorkspacePage
            executions={executions}
            subtasks={subtasks}
            scenarioDetail={scenarioDetail}
            scenarioCatalog={scenarioCatalog}
            selectedScenarioId={selectedScenarioId}
            scenarioObjective={scenarioObjective}
            scenarioInputs={scenarioInputs}
            onChangeScenarioId={setSelectedScenarioId}
            onChangeScenarioObjective={setScenarioObjective}
            onChangeScenarioInput={handleChangeScenarioInput}
            selectedPlanId={selectedPlanId}
            usageHint={usageHint}
            onChangePlanId={setSelectedPlanId}
            onSelectExecution={handleSelectExecution}
            onRunScenario={handleRunScenario}
            isLoading={loadingExecutions}
            errorMessage={executionsError}
          />
        )}
        {section === 'logs' && (
          <LogsPage
            selectedExecutionId={selectedExecutionId}
            events={events}
            isLoading={loadingTimeline}
            errorMessage={timelineError}
          />
        )}
        {section === 'agents' && <AgentsPage agents={agents} isLoading={loadingAgents} errorMessage={agentsError} />}
        {section === 'billing' && (
          <BillingPage
            projectId={billingProjectId}
            overview={billingOverview}
            invoices={billingInvoices}
            usageItems={billingUsageItems}
            isLoading={loadingBilling}
            errorMessage={billingError}
          />
        )}
      </main>
    </div>
  )
}
