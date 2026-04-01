# Optimus Platform

Plataforma modular de agentes de engenharia e operações com duas camadas:

1. **Núcleo de agentes** (FastAPI + core modular)
2. **Produto visual** (React + Tailwind)

## Fase 2 — status

### Fechado nesta iteração
- Persistência real de usuários no PostgreSQL (`users`) com login sem bootstrap in-memory em runtime real.
- Sessão stateful em Redis com login/logout e validação em rotas privadas.
- RBAC inicial funcional por role (`admin`, `operator`, `viewer`) em rotas de execução.
- Fluxo operacional completo: API cria execução, enfileira no ARQ, worker processa com lock Redis, persiste status e auditoria.
- Frontend operacional consumindo API real em dashboard/workspace/logs, com estados loading/empty/error.

### Decisões técnicas
- Persistência PostgreSQL: **psycopg 3 + SQL versionado**.
- Sessão: **token stateful em Redis** (TTL/revogação).
- Fila: **ARQ sobre Redis**.
- Locks efêmeros: Redis `SET NX EX` por `execution_id`.
- Auditoria mínima: `queued`, `enqueued`, `started`, `completed`, `failed`, `lock_skipped`.

## Endpoints
- `GET /health/`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /executions/run`
- `GET /executions/`
- `GET /executions/{id}/timeline`

## Execução local

### 1) PostgreSQL + Redis
Suba os serviços localmente (docker compose local, serviço gerenciado ou instalação local), aplique `backend/sql/001_init.sql` no PostgreSQL.

### 2) Backend API
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn optimus_backend.main:app --reload --port 8000
```

### 3) Worker ARQ
```bash
cd backend
arq optimus_backend.infrastructure.queue.worker.WorkerSettings
```

### 4) Frontend
```bash
cd frontend
npm install
npm run dev
```

## Testes
```bash
python -m compileall backend/src frontend/src
cd backend && pytest
```

### Teste de integração real (PostgreSQL + Redis + ARQ)
```bash
cd backend
INTEGRATION_REAL=1 DATABASE_URL=postgresql://... REDIS_URL=redis://... REDIS_HOST=... REDIS_PORT=... pytest -m integration -q
```
