# Arquitetura recomendada

## Fase 4 — complementos obrigatórios
- Idempotência por `idempotency_key` com janela temporal de reuso.
- Budget por execução com cutoff automático e `bounded_completion`.
- Rate limit por tool e por projeto usando Redis.
- Enum de severidade único (`low|medium|high|critical`) backend+frontend.
- Sanitização reforçada com redação de secrets, truncamento e hash de payload.
- Memória versionada com `version`, `supersedes_id` e status `deprecated`.

## Orquestração
- Subtask com `depends_on`, `handoff_reason`, `attempt`.
- Limite de handoffs (3).

## Tool execution pipeline
1. Policy
2. Guard (pre)
3. Rate limit
4. Execução
5. Guard (post)
6. Audit

## Cenários operacionais
- run/detail/timeline com critérios de sucesso/falha e trilha auditável.
