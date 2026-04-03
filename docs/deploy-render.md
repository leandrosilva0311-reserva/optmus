# Deploy no Render (Passo 1 — Infra produção)

Este passo prepara a infraestrutura mínima para o backend:

- PostgreSQL gerenciado
- Redis gerenciado
- serviço web FastAPI

## Arquivos

- `deploy/render.yaml`: blueprint com backend + Redis + Postgres.
- `backend/.env.production.example`: referência das variáveis obrigatórias.

## Como aplicar

1. No Render, criar Blueprint a partir do repositório.
2. Selecionar `deploy/render.yaml`.
3. Definir secret `DEFAULT_TENANT_API_KEY` (não usar valor default local).
4. Confirmar que `DATABASE_URL` e `REDIS_URL` foram vinculados pelos recursos gerenciados.
5. Fazer deploy.

## Verificação pós deploy

- `/health/` deve responder `200`.
- Rotas protegidas (ex.: `/executions/`) devem exigir `X-API-Key`.
- Com API key válida, fluxo segue para autenticação de sessão.

## Observação

Este passo **não** inclui persistência real de tenants/api keys em Postgres.
Isso entra no próximo bloco (substituir tenancy in-memory por repositories Postgres/Redis).
