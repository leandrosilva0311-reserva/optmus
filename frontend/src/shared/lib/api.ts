const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type LoginResponse = { session_id: string; role: string }
export type Execution = {
  id: string
  project_id: string
  objective: string
  agent: string
  status: string
  summary?: string | null
  error?: string | null
  duration_ms?: number | null
  created_at: string
}

export type Subtask = {
  id: string
  execution_id: string
  agent: string
  title: string
  depends_on: string[]
  status: string
  result_summary?: string | null
  created_at: string
}

export type AuditEvent = {
  id: string
  execution_id: string
  event_type: string
  message: string
  created_at: string
}

export type AgentCatalogItem = {
  key: string
  title: string
  responsibilities: string[]
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!response.ok) throw new Error('Login failed')
  return response.json()
}

export async function listExecutions(sessionId: string): Promise<Execution[]> {
  const response = await fetch(`${API_BASE}/executions/`, { headers: { 'X-Session-Id': sessionId } })
  if (!response.ok) throw new Error('Failed to load executions')
  return response.json()
}

export async function getSubtasks(sessionId: string, executionId: string): Promise<Subtask[]> {
  const response = await fetch(`${API_BASE}/executions/${executionId}/subtasks`, {
    headers: { 'X-Session-Id': sessionId },
  })
  if (!response.ok) throw new Error('Failed to load subtasks')
  return response.json()
}

export async function getTimeline(sessionId: string, executionId: string): Promise<AuditEvent[]> {
  const response = await fetch(`${API_BASE}/executions/${executionId}/timeline`, {
    headers: { 'X-Session-Id': sessionId },
  })
  if (!response.ok) throw new Error('Failed to load timeline')
  return response.json()
}

export async function getAgentCatalog(sessionId: string): Promise<AgentCatalogItem[]> {
  const response = await fetch(`${API_BASE}/agents/catalog`, {
    headers: { 'X-Session-Id': sessionId },
  })
  if (!response.ok) throw new Error('Failed to load agents')
  return response.json()
}

export async function logout(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/logout`, {
    method: 'POST',
    headers: { 'X-Session-Id': sessionId },
  })
  if (!response.ok) throw new Error('Logout failed')
}
