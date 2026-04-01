# Arquitetura recomendada

## Princípios
- Modularidade estrita
- Separação de responsabilidades
- Segurança e auditabilidade por padrão
- Observabilidade nativa
- Preparação para multi-tenant

## Fase 2 — decisões finais
1. Persistência PostgreSQL com **psycopg 3 + SQL migrations versionadas**.
2. Sessão com **session token stateful em Redis**.
3. Autenticação com usuário real persistido em `users` no PostgreSQL.
4. RBAC inicial por roles (`admin`, `operator`, `viewer`) em rotas de execução.
5. Locks efêmeros com Redis `SET NX EX` por `execution_id`.
6. Eventos auditáveis mínimos: `queued`, `enqueued`, `started`, `completed`, `failed`, `lock_skipped`.

## Camadas
- **API:** rotas HTTP e controle de acesso.
- **Application:** casos de uso de autenticação, execução e consulta.
- **Core:** engine de agentes/orquestração/guards/telemetria.
- **Domain:** entidades e portas.
- **Infrastructure:** implementações PostgreSQL/Redis/ARQ.

## Fluxo operacional ponta a ponta
1. Usuário faz login (`/auth/login`) e recebe `session_id`.
2. Rotas privadas validam sessão no Redis + role no PostgreSQL.
3. API cria execução (`queued`) e enfileira no ARQ.
4. Worker aplica lock Redis por execução, marca `running`, executa engine e persiste resultado.
5. Dashboard/Workspace/Logs consomem execuções e timeline da API.
