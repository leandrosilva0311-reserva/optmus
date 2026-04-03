# Engineering Report Contract v1

Este documento define o payload dedicado de `engineering_report` persistido em auditoria.

## event_type

- `engineering_report`

## payload

```json
{
  "execution_id": "string",
  "scenario_id": "code_analysis|bug_diagnosis|refactor_suggestion|patch_review",
  "diagnosis": "string",
  "evidence": ["string"],
  "recommendations": ["string"],
  "risk_level": "low|medium|high|critical",
  "urgency": "low|medium|high|immediate",
  "execution_plan": [
    {
      "step_id": "s1",
      "title": "string",
      "description": "string",
      "expected_outcome": "string"
    }
  ],
  "generated_at": "ISO-8601"
}
```

## Endpoint dedicado

- `GET /scenarios/{execution_id}/engineering-report`

## Compatibilidade

- `business_block` permanece disponível para impacto operacional/comercial.
- `engineering_report` centraliza diagnóstico técnico estruturado.

## Persistência como artefato recuperável

- Além do evento de auditoria `engineering_report`, o conteúdo é persistido como artefato de memória (`entry_type=engineering_report`) para leitura estável por execução.

## generated_at

- `generated_at` deve refletir o instante de geração no worker no momento em que o relatório técnico é montado.

## Conector local desta fase

- O conector local é validado pela presença de `.git` no diretório raiz.
- Escopo desta fase: operações de filesystem (`list_files`, `fetch_file`, `search`).
- Não executa comandos Git (`status`, `log`, `diff`, checkout, etc.).

## Limites de hidratação automática (repo_path -> files)

- Máximo de arquivos: `40`
- Máximo por arquivo: configurável por ambiente em `LOCAL_CONNECTOR_MAX_FILE_BYTES`
- Máximo total agregado: `1_500_000 bytes`
- Diretórios ignorados e extensões permitidas também são configuráveis por ambiente.

## Repo enrichment opt-in por cenário

- Enrichment por repositório local só é aplicado de forma explícita (`repo_enrichment.enabled=true`).
- Cenários habilitados nesta fase: `bug_diagnosis` e `refactor_suggestion`.
- `code_analysis` não aplica enrichment automático por padrão.

## Auditoria de enrichment

- Cada execução registra `scenario_repo_enrichment` com payload objetivo:
  - `attempted`
  - `applied`
  - `listed_files`
  - `selected_files`
  - `search_hits`
  - `ranking_preview` (com `path`, `score`, `reasons`, `module_key`)
  - `skipped_reason`

## Heurística de priorização (fase local)

- Pipelines distintos:
  - `bug_diagnosis`: prioriza sinais de `observed_error` e hits de busca.
  - `refactor_suggestion`: prioriza alinhamento com `objective` + `file_pattern`.
- Ranking retorna explicabilidade mínima com score + razões.
- Diversidade simples por módulo é aplicada para reduzir concentração de arquivos semelhantes.

## Retorno mínimo de search(query)

Cada ocorrência deve retornar:

```json
{
  "path": "src/module.py",
  "line_number": 42,
  "line_range": [42, 42],
  "snippet": "trecho encontrado"
}
```
