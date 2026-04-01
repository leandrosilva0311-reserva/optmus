# Arquitetura recomendada

## Princípios
- Modularidade estrita
- Separação de responsabilidades
- Segurança e auditabilidade por padrão
- Observabilidade nativa
- Preparação para multi-tenant

## Decisões técnicas da Fase 2
1. Persistência PostgreSQL com **psycopg 3 + SQL migrations versionadas** (equivalente robusto ao stack ORM).
2. Sessão com **session token stateful em Redis** (não JWT stateless nesta fase).
3. Auditoria mínima persistida: `queued`, `enqueued`, `started`, `completed`, `failed`, `lock_skipped`.
4. Locks efêmeros com Redis `SET NX EX` por `execution_id`.
5. Frontend com estados reais de `loading`, `empty`, `error` por página operacional.

## Camadas

### API (`api/`)
Camada HTTP, autenticação de sessão, validação e serialização.

### Application (`application/use_cases/`)
Casos de uso explícitos (`authenticate`, `start_execution`, `list_executions`).

### Core (`core/`)
Mecanismo do agente e módulos especializados (orchestrator, guard, context, telemetry, provider).

### Domain (`domain/`)
Entidades e contratos (ports) sem dependência de framework.

### Infrastructure (`infrastructure/`)
Implementações concretas de PostgreSQL, Redis, ARQ e segurança.

## Persistência
- **PostgreSQL** como estado principal (execuções + auditoria).
- **Redis** para sessão, locks efêmeros e suporte a fila.

## Fila assíncrona
- **ARQ** foi escolhido por integração natural com Redis e menor sobrecarga operacional.
- Request HTTP cria execução e enfileira job sem acoplar à execução síncrona.

## Segurança
- Login com validação de credenciais.
- Sessão validada por header (`X-Session-Id`) em rotas protegidas.
- `ExecutionGuard` mantém bloqueio de ações destrutivas.

## Observabilidade
- Eventos de execução são persistidos como timeline auditável por execução.
