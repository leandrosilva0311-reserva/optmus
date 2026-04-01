# Arquitetura recomendada

## Fase 3 — foco
- Tooling real via adapters/interfaces
- Memória persistente por projeto com fluxo pending->approved
- Context Builder determinístico com ranking e justificativa
- Orquestração com subtarefas e depends_on
- Auditoria sanitizada

## Ordem mandatória de execução de ferramentas
1. Policy
2. Guard (pre)
3. Execução da ferramenta
4. Guard (post)
5. Audit

## Tool adapters
- FilesystemTool: sandbox project_root + anti path traversal
- TerminalTool: allowlist + timeout + limite de output + sem shell arbitrário
- HttpTool: domain allowlist + method allowlist + timeout + retry

## Modelo de memória
- Campos: `type`, `source`, `confidence`, `status`
- Status: `pending` -> `approved`

## Orquestração
- Subtasks com `depends_on`
- Eventos obrigatórios de subtarefa: `subtask_started`, `subtask_completed` (e falha quando aplicável)
- Audit trail sanitizado (sem payload bruto completo)
