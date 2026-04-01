import { useEffect, useState } from 'react'

import { LoginForm } from '../domains/auth/components/login-form'
import { DashboardPage } from '../domains/dashboard/page'
import { LandingPage } from '../domains/landing/page'
import { LogsPage } from '../domains/logs/page'
import { WorkspacePage } from '../domains/workspace/page'
import { TopNav } from '../shared/components/top-nav'
import { AuditEvent, Execution, getTimeline, listExecutions, login, logout } from '../shared/lib/api'

export function AppRouter() {
  const [section, setSection] = useState('landing')
  const [sessionId, setSessionId] = useState<string | null>(localStorage.getItem('session_id'))
  const [role, setRole] = useState<string | null>(localStorage.getItem('role'))
  const [executions, setExecutions] = useState<Execution[]>([])
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null)
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [loadingExecutions, setLoadingExecutions] = useState(false)
  const [executionsError, setExecutionsError] = useState<string | null>(null)
  const [loadingTimeline, setLoadingTimeline] = useState(false)
  const [timelineError, setTimelineError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return

    async function loadExecutions() {
      setLoadingExecutions(true)
      setExecutionsError(null)
      try {
        const data = await listExecutions(sessionId)
        setExecutions(data)
      } catch {
        setExecutionsError('Não foi possível carregar execuções.')
        setExecutions([])
      } finally {
        setLoadingExecutions(false)
      }
    }

    loadExecutions()
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
      const timeline = await getTimeline(sessionId, executionId)
      setEvents(timeline)
      setSection('logs')
    } catch {
      setTimelineError('Falha ao carregar timeline da execução.')
      setEvents([])
      setSection('logs')
    } finally {
      setLoadingTimeline(false)
    }
  }

  async function handleLogout() {
    if (sessionId) {
      try {
        await logout(sessionId)
      } catch {
        // logout local mesmo com falha remota
      }
    }
    localStorage.removeItem('session_id')
    localStorage.removeItem('role')
    setSessionId(null)
    setRole(null)
    setExecutions([])
    setEvents([])
    setSelectedExecutionId(null)
    setExecutionsError(null)
    setTimelineError(null)
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
            onSelectExecution={handleSelectExecution}
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
      </main>
    </div>
  )
}
