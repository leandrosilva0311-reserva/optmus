# Optimus Platform

Plataforma modular de agentes de engenharia e operações com duas camadas:

1. **Núcleo de agentes** (FastAPI + core modular)
2. **Produto visual** (React + Tailwind)

## Fase 2 (implementada)

### Decisões técnicas
- Persistência: **psycopg 3 + SQL versionado** para PostgreSQL.
- Sessão: **token stateful em Redis** (TTL e revogação).
- Fila: **ARQ** sobre Redis.
- Locks efêmeros: Redis `SET NX EX` por execução.
- Frontend operacional com estados reais: `loading`, `empty`, `error`.

### Entregas principais
- Persistência preparada para **PostgreSQL** (repositórios concretos) e fallback em memória para testes locais.
- Sessões e locks com **Redis** (repositórios concretos) e fallback em memória para testes.
- Execução assíncrona desacoplada via estrutura de **ARQ** (`queue/worker.py`, `arq_queue.py`).
- Autenticação baseada em credenciais + sessão (`/auth/login`) com proteção de rotas por `X-Session-Id`.
- Dashboard/workspace/logs no frontend consumindo execuções reais da API.

## Endpoints
- `GET /health/`
- `POST /auth/login`
- `POST /executions/run` (enfileira execução)
- `GET /executions/` (lista execuções)
- `GET /executions/{id}/timeline` (timeline auditável)

## Execução local

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn optimus_backend.main:app --reload --port 8000
```

### Worker ARQ
```bash
cd backend
arq optimus_backend.infrastructure.queue.worker.WorkerSettings
```

### Frontend
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
