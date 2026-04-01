# Plano por fases

## Fase 1 — Fundação ✅
- Estrutura de diretórios modular
- FastAPI base
- Núcleo inicial de agentes
- Frontend base React + Tailwind

## Fase 2 — Persistência, fila e auth ✅
- Repositórios para PostgreSQL (execuções e auditoria)
- Sessão com Redis
- Estrutura de jobs assíncronos com ARQ
- Auth/login com sessão e proteção de rotas
- Dashboard/Workspace/Logs iniciais no frontend

## Fase 3 — Orquestração avançada
- DAG de dependências entre agentes
- Paralelismo controlado
- Aprovação por política em ações críticas

## Fase 4 — Produto SaaS robusto
- Admin area completa
- RBAC completo
- Billing real
- Observabilidade operacional avançada

## Fase 5 — Integrações e Kaiso-ready (ajustada)

### 5.1 Governança de cenários
- Schema de entrada obrigatório por cenário (inputs mínimos validados antes da execução).
- Definition of Done por cenário com critérios objetivos de sucesso/falha.
- Estados terminais parciais preparados para cenários WhatsApp e KDS/POS:
  - `partial_success`
  - `external_dependency_unavailable`
  - `manual_validation_required`

### 5.2 Ferramentas formais de diagnóstico
- `KaisoLogCorrelationTool` com chaves obrigatórias:
  - `request_id`
  - `execution_id`
  - `order_id`
  - `restaurant_id`
  - janela temporal (`time_window_start`, `time_window_end`)
- `KaisoQueueInspectionTool` com métricas mínimas:
  - `backlog_size`
  - `oldest_job_age_seconds`
  - `failed_jobs_count`
  - `estimated_processing_latency_ms`

### 5.3 Relatório final com bloco de negócio
- Impacto operacional
- Impacto comercial
- Severidade
- Ação imediata
- Responsável sugerido

### 5.4 Arquitetura e qualidade
- Adapters/interfaces obrigatórios para integrações novas.
- Auditoria completa com trilha por execução.
- Cobertura de testes para lógica crítica.
