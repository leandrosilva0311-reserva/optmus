# Optimus Platform

## Fase 4 (operacional)

### Regras explícitas implementadas
1. **Janela de idempotência:** 30 minutos por `idempotency_key` (`project + scenario + objective_normalized`).
2. **Rate limit:** por projeto e por tool (janela de 60s). Padrão: project=80/min, tool=20/min.
3. **Prioridade de cutoff de budget:** `max_duration_ms` > `max_tool_calls` > `max_steps`.
4. **Versionamento de memória:**
   - nova entrada cria versão adicional;
   - se conteúdo muda, versão anterior vira `deprecated` e nova referencia `supersedes_id`.

### Endpoints de cenário
- `POST /scenarios/run`
- `GET /scenarios/{execution_id}`
- `GET /scenarios/{execution_id}/timeline`

### Execução local
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

### Testes
```bash
python -m compileall backend/src frontend/src
cd backend && pytest -q
```
