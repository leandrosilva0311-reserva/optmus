# Engineering Scenarios v1 (Optimus)

Cenários genéricos iniciais para plataforma SaaS de agentes de engenharia:

- `code_analysis`
- `bug_diagnosis`
- `refactor_suggestion`
- `patch_review`

## Saída estruturada obrigatória
Todos os cenários de engenharia devem produzir:

- `diagnosis`
- `evidence`
- `recommendations`
- `risk_level`
- `urgency`
- `execution_plan` (lista de passos estruturados)

## Observações de compatibilidade
- Aliases legados são resolvidos fora do core via camada de aplicação.
- `patch_review` exige `diff_text` obrigatório.
- `files` é modelado como lista explícita de `{path, content}`.
