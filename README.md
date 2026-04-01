# Optimus Platform

## Fase 3 (em implementação operacional)

Esta entrega adiciona base funcional para tooling real, memória/contexto evoluídos, orquestração por subtarefas e UI operacional de agentes.

### Padrões de segurança incorporados
- Envelope padrão de tool execution: `status`, `duration_ms`, `truncated`, `error`.
- Ordem fixa de execução de tooling: **policy -> guard(pre) -> execução -> guard(post) -> audit**.
- Terminal tool com allowlist, timeout curto, limite de output e sem shell arbitrário.
- Filesystem tool com sandbox em `project_root` e proteção contra path traversal.
- HTTP tool com allowlist de domínios, restrição de verbos, timeout e retry controlado.

### Fase 3 — fluxo funcional
1. API cria execução e subtarefas com `depends_on`.
2. Worker processa subtarefas respeitando dependências.
3. Worker registra eventos de subtarefa e envelope sanitizado de tool execution.
4. Resultado final alimenta memória persistente em estado `pending` para posterior aprovação (`approved`).
5. Frontend exibe execução, subtarefas, timeline e catálogo de agentes com estados loading/empty/error.

## Endpoints relevantes
- `GET /agents/catalog`
- `POST /executions/run`
- `GET /executions/`
- `GET /executions/{id}/subtasks`
- `GET /executions/{id}/timeline`

## Execução local
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn optimus_backend.main:app --reload --port 8000
```

```bash
cd backend
arq optimus_backend.infrastructure.queue.worker.WorkerSettings
```

```bash
cd frontend
npm install
npm run dev
```
