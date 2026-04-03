const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type Severity = 'low' | 'medium' | 'high' | 'critical' | 'pending'
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
  handoff_reason?: string | null
  attempt?: number
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

export type ScenarioDefinitionOfDone = {
  success_criteria: string[]
  failure_criteria: string[]
}

export type ScenarioCatalogItem = {
  scenario_id: string
  name: string
  required_inputs: string[]
  definition_of_done: ScenarioDefinitionOfDone
  supported_terminal_states: string[]
  business_value: string
  recommended_for: string[]
  estimated_runtime_minutes: number
  onboarding_steps: string[]
}

export type ScenarioBusinessBlock = {
  operational_impact: string
  commercial_impact: string
  severity: Severity
  immediate_action: string
  suggested_owner: string
}

export type ScenarioDetail = {
  execution_id: string
  project_id: string
  scenario_id: string
  status: string
  summary?: string | null
  max_steps: number
  max_tool_calls: number
  max_duration_ms: number
  created_at: string
  required_inputs: string[]
  definition_of_done: ScenarioDefinitionOfDone
  supported_terminal_states: string[]
  final_business_block: ScenarioBusinessBlock | null
}

export type UsageSnapshot = {
  plan_id: string
  daily_limit: number
  consumed_today: number
  remaining_today: number
}

export type RunScenarioResponse = {
  execution_id: string
  status: string
  reused: boolean
  usage: UsageSnapshot
}

export type BillingInvoice = {
  id: string
  project_id: string
  period_start: string
  period_end: string
  status: string
  total_cents: number
  created_at: string
}

export type BillingInvoiceTransition = {
  id: string
  invoice_id: string
  from_status: string
  to_status: string
  changed_by: string
  changed_at: string
}

export type BillingInvoiceHistoryEntry = BillingInvoice & {
  item_count: number
  transitions: BillingInvoiceTransition[]
}

export type BillingUsageHistoryItem = { event_date: string; units: number }

export type BillingUsageHistoryResponse = {
  project_id: string
  items: BillingUsageHistoryItem[]
}

export type BillingSchedulerRunHistoryItem = {
  id: string
  started_at: string
  finished_at: string
  success: boolean
  attempts: number
  alert_required: boolean
  processed_subscriptions: number
  generated_invoices: number
  failed_subscriptions: number
  duration_ms: number
  error: string | null
  warnings: string[]
}

export type BillingAdminOverview = {
  latest_scheduler_run: BillingSchedulerRunHistoryItem | null
  recent_alerts: BillingSchedulerRunHistoryItem[]
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

export async function listScenarioCatalog(sessionId: string): Promise<ScenarioCatalogItem[]> {
  const response = await fetch(`${API_BASE}/scenarios/catalog`, {
    headers: { 'X-Session-Id': sessionId },
  })
  if (!response.ok) throw new Error('Failed to load scenario catalog')
  return response.json()
}

export async function runScenario(
  sessionId: string,
  projectId: string,
  scenarioId: string,
  objective: string,
  inputs: Record<string, string>,
  planId: string = "starter"
): Promise<RunScenarioResponse> {
  const response = await fetch(`${API_BASE}/scenarios/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Session-Id': sessionId },
    body: JSON.stringify({ project_id: projectId, scenario_id: scenarioId, objective, inputs, plan_id: planId }),
  })
  if (!response.ok) throw new Error('Failed to run scenario')
  return response.json()
}

export async function getScenarioDetail(sessionId: string, executionId: string): Promise<ScenarioDetail> {
  const response = await fetch(`${API_BASE}/scenarios/${executionId}`, {
    headers: { 'X-Session-Id': sessionId },
  })
  if (!response.ok) throw new Error('Failed to load scenario detail')
  return response.json()
}

export async function getScenarioTimeline(sessionId: string, executionId: string): Promise<AuditEvent[]> {
  const response = await fetch(`${API_BASE}/scenarios/${executionId}/timeline`, {
    headers: { 'X-Session-Id': sessionId },
  })
  if (!response.ok) throw new Error('Failed to load scenario timeline')
  return response.json()
}

export async function listBillingInvoices(sessionId: string, projectId: string): Promise<BillingInvoice[]> {
  const response = await fetch(`${API_BASE}/billing/invoices?project_id=${encodeURIComponent(projectId)}`, {
    headers: { 'X-Session-Id': sessionId },
  })
  if (!response.ok) throw new Error('Failed to load billing invoices')
  return response.json()
}

export async function getBillingInvoiceHistory(sessionId: string, projectId: string): Promise<BillingInvoiceHistoryEntry[]> {
  const response = await fetch(`${API_BASE}/billing/invoices/history?project_id=${encodeURIComponent(projectId)}`, {
    headers: { 'X-Session-Id': sessionId },
  })
  if (!response.ok) throw new Error('Failed to load invoice history')
  const payload = await response.json()
  return payload.items
}

export async function getBillingUsagePeriod(
  sessionId: string,
  projectId: string,
  periodStart: string,
  periodEnd: string
): Promise<BillingUsageHistoryResponse> {
  const query = new URLSearchParams({
    project_id: projectId,
    period_start: periodStart,
    period_end: periodEnd,
  })
  const response = await fetch(`${API_BASE}/billing/usage/period?${query.toString()}`, {
    headers: { 'X-Session-Id': sessionId },
  })
  if (!response.ok) throw new Error('Failed to load usage period')
  return response.json()
}

export async function getBillingAdminOverview(sessionId: string): Promise<BillingAdminOverview> {
  const response = await fetch(`${API_BASE}/billing/admin/overview`, {
    headers: { 'X-Session-Id': sessionId },
  })
  if (!response.ok) throw new Error('Failed to load billing admin overview')
  return response.json()
}
