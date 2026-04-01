import { useEffect, useState } from 'react'

import { LoginForm } from '../domains/auth/components/login-form'
import { AgentsPage } from '../domains/agents/page'
import { DashboardPage } from '../domains/dashboard/page'
import { LandingPage } from '../domains/landing/page'
import { LogsPage } from '../domains/logs/page'
import { WorkspacePage } from '../domains/workspace/page'
import { TopNav } from '../shared/components/top-nav'
import {
  AgentCatalogItem,
  AuditEvent,
  Execution,
  ScenarioDetail,
  Subtask,
  getAgentCatalog,
  getScenarioDetail,
  getScenarioTimeline,
  getSubtasks,
  getTimeline,
  listExecutions,
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
  const [scenarioDetail, setScenarioDetail] = useState<ScenarioDetail | null>(null)
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null)
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [loadingExecutions, setLoadingExecutions] = useState(false)
  const [executionsError, setExecutionsError] = useState<string | null>(null)
  const [loadingTimeline, setLoadingTimeline] = useState(false)
  const [timelineError, setTimelineError] = useState<string | null>(null)
  const [loadingAgents, setLoadingAgents] = useState(false)
  const [agentsError, setAgentsError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return

    async function loadBootData() {
      setLoadingExecutions(true)
      setLoadingAgents(true)
      setExecutionsError(null)
      setAgentsError(null)

      try {
        const [execData, agentData] = await Promise.all([listExecutions(sessionId), getAgentCatalog(sessionId)])
        setExecutions(execData)
        setAgents(agentData)
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

  async function handleRunScenario() {
    if (!sessionId) return
    try {
      const result = await runScenario(sessionId, 'default', 'health_check', 'validar saúde operacional')
      const [detail, timeline] = await Promise.all([
        getScenarioDetail(sessionId, result.execution_id),
        getScenarioTimeline(sessionId, result.execution_id),
      ])
      setScenarioDetail(detail)
      setEvents(timeline)
      setSelectedExecutionId(result.execution_id)
      setSection('logs')
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
        {section === 'agents' && (
          <AgentsPage agents={agents} isLoading={loadingAgents} errorMessage={agentsError} />
        )}
      </main>
    </div>
  )
}
