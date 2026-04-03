# Fase 5 — Metering persistente e Billing por plano

## Status atual
- Base in-memory ativa em runtime de teste/desenvolvimento rápido.
- `PostgresUsageMeter` implementado para produção e migração SQL inicial de billing criada (`backend/sql/002_billing_init.sql`).
- Enforcement agora prioriza plano da `subscription` ativa por projeto quando disponível.
- Warnings de uso em 80% e 95% antes do bloqueio.
- Frontend segue pendente apenas de validação final de build quando o ambiente liberar `npm install`.

## 1) Persistência real de usage metering (substituir in-memory)

### Objetivo
Trocar `InMemoryUsageMeter` por um adapter persistente e compartilhado entre réplicas.

### Modelo inicial (PostgreSQL)
Tabela proposta `usage_events`:
- `id` (uuid)
- `project_id` (text)
- `plan_id` (text)
- `scenario_id` (text)
- `units` (int)
- `event_date` (date)
- `created_at` (timestamptz)

Tabela agregada `usage_daily_counters`:
- `project_id`
- `plan_id`
- `event_date`
- `consumed_units`
- PK composta (`project_id`, `plan_id`, `event_date`)

### Estratégia de consumo atômico
1. Transação SQL com `SELECT ... FOR UPDATE` em `usage_daily_counters`.
2. Carregar limite do plano.
3. Validar consumo.
4. Incrementar contador e inserir evento em `usage_events`.
5. Commit.

### Contrato de adapter
Manter protocolo `UsageMeter` em `domain/ports.py`.
Implementações:
- `InMemoryUsageMeter` (dev/test)
- `PostgresUsageMeter` (produção)

## 2) Assinatura como fonte de verdade do enforcement

1. Buscar `subscription` ativa por `project_id`.
2. Resolver `plan_id` efetivo pela assinatura.
3. Só usar `plan_id` da requisição como fallback quando não houver assinatura.
4. Aplicar limites e warnings sobre o plano efetivo.

## 3) Estratégia inicial de billing/assinatura real

### Entidades mínimas
- `subscriptions`: plano ativo por projeto, status, ciclo, datas.
- `plan_definitions`: limites e preço por plano.
- `invoices` / `invoice_items`: cobrança consolidada por período.

### Fluxo comercial mínimo
1. Projeto possui assinatura (`starter|growth|enterprise`).
2. Cada execução de cenário gera evento de uso.
3. No fechamento do ciclo, gerar invoice com consumo e excedentes (quando aplicável).
4. Expor no frontend painel de uso atual, limite e projeção do ciclo.

### Regras de produto (MVP)
- Hard limit diário por plano para proteção operacional.
- Soft warning em 80% do limite.
- Warning crítico em 95% do limite.
- Excedente bloqueado com HTTP 429 + mensagem comercial para upgrade.

## 4) Ordem de implementação recomendada
1. SQL migration + `PostgresUsageMeter`.
2. DI por ambiente (`test/dev/prod`).
3. APIs mínimas: planos, assinatura ativa e uso atual.
4. Painel de billing no frontend.
5. Jobs de fechamento de ciclo e emissão de invoice.
