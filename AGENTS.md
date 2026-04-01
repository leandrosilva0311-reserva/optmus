# AGENTS.md — Optimus

## Objetivo
Manter arquitetura modular, auditável, segura e preparada para evolução multi-tenant.

## Regras de engenharia
1. Não criar arquivos monolíticos.
2. Cada módulo deve ter responsabilidade única.
3. Evitar acoplamento entre `core`, `application`, `infrastructure` e `api`.
4. Toda lógica crítica precisa de teste.
5. Erros devem ser padronizados.
6. Novas integrações devem passar por interfaces em `core/provider` ou `core/tool_router`.
7. Não introduzir dependências implícitas.

## Convenções
- Python: tipagem obrigatória em funções públicas.
- Frontend: organização por domínio em `frontend/src/domains`.
- Logs estruturados com `execution_id`, `agent_id`, `event_type`.

## Pull requests
- Descrever contexto, decisão técnica e impacto por camada.
- Listar riscos e próximos passos.
