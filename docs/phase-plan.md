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

## Fase 5 — Plataforma vendável, genérica e multi-domínio

### 5.1 Biblioteca de cenários genéricos (vendáveis)
- Cenários orientados a qualquer SaaS/API, sem acoplamento por cliente:
  - `public_api_health`
  - `checkout_flow_validation`
  - `queue_health`
  - `incident_timeline_reconstruction`
- Cada cenário define:
  - schema de entrada obrigatório
  - Definition of Done objetivo (sucesso/falha)
  - estados parciais (`partial_success`, `external_dependency_unavailable`, `manual_validation_required`)

### 5.2 Tools genéricas com contratos estáveis
- Tools de plataforma sem naming de domínio:
  - `log_correlation`
  - `queue_inspection`
  - `http_probe`
  - `workflow_trace`
- Contratos focados em capacidades (correlação, inspeção, validação), não em sistemas específicos.

### 5.3 Agents independentes de domínio
- Agentes padrão de produto:
  - `BackendAgent`
  - `OpsAgent`
  - `QAAgent`
  - `AnalystAgent`
- Especialização por domínio deve ocorrer via contexto + adapters, sem renomear agentes por cliente.

### 5.4 Camada de adapters/domínios
- Introduzir camada explícita de integração por domínio (`infrastructure/adapters/<domain>`).
- `Kaiso` passa a ser somente um adapter de integração, implementando interfaces genéricas.
- Permitir adicionar novos domínios (ex.: `shopify`, `erp_x`, `payments_y`) sem alterar core/application.

### 5.5 Relatório final de negócio (reutilizável)
- Estrutura comum para qualquer cenário:
  - impacto operacional
  - impacto comercial
  - severidade
  - ação imediata
  - responsável sugerido

### 5.6 Qualidade e governança
- Adapters/interfaces obrigatórios para novas integrações.
- Auditoria completa com `execution_id`, `agent_id`, `event_type`.
- Testes obrigatórios para lógica crítica e contratos de adapter.
