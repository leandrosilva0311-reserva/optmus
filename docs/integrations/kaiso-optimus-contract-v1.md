# Kaiso -> Optimus Integration Contract (v1)

## Endpoint externo v1
Nesta fase, o contrato externo usa diretamente:

- `POST /scenarios/run`

Sem façade adicional, salvo necessidade real futura.

## Autenticação
Headers obrigatórios:

- `Authorization: Bearer <OPTIMUS_API_KEY>` **ou** `X-API-Key: <OPTIMUS_API_KEY>`
- `Content-Type: application/json`
- `X-Request-Id: <uuid/string-correlacao>` (obrigatório para rastreabilidade ponta-a-ponta)

Variáveis esperadas no backend Kaiso:

- `OPTIMUS_API_URL`
- `OPTIMUS_API_KEY`
- `OPTIMUS_PROJECT_ID`

Escopo mínimo da key:

- `scenarios:run`

## Timeout e retry
- Timeout de requisição recomendado: **5s** (connect+read, total de chamada)
- Retry básico: até **2 tentativas adicionais** (total 3), somente para erros transitórios:
  - timeout/network
  - HTTP `408`, `429`, `500`, `502`, `503`, `504`
- Sem retry para `400`, `401`, `403`, `404`, `422`.

## Request (schema real)
`POST /scenarios/run`

```json
{
  "project_id": "<OPTIMUS_PROJECT_ID>",
  "scenario_id": "code_analysis",
  "objective": "Diagnosticar hotspots de acoplamento",
  "inputs": {
    "stack": "python-fastapi",
    "objective": "reduzir acoplamento entre módulos",
    "files": [
      {"path": "src/service.py", "content": "def handler(): return 1"}
    ]
  },
  "plan_id": "starter"
}
```

### Observação sobre `plan_id`
- `plan_id` é opcional.
- Se houver assinatura ativa no projeto, o plano ativo é usado.
- Se **não** houver assinatura ativa e `plan_id` não for enviado, fallback para `starter`.

### Modelagem de arquivos nesta fase
- `files` deve ser uma lista explícita de objetos `{path, content}`.
- Essa modelagem é agnóstica de Git/GitHub e prepara conectores futuros sem acoplamento imediato.

## Response de sucesso (200)
```json
{
  "execution_id": "uuid",
  "status": "queued",
  "reused": false,
  "usage": {
    "plan_id": "starter",
    "daily_limit": 20,
    "consumed_today": 1,
    "remaining_today": 19,
    "warning_level": "ok"
  },
  "request_id": "<X-Request-Id>"
}
```

Além disso, a resposta ecoa `X-Request-Id` no header.

## Erros esperados
- `400`: payload inválido ou regra de negócio
- `401`: credencial ausente/inválida
- `403`: escopo insuficiente (`scenarios:run`)
- `429`: limite de uso excedido
- `5xx`: falha interna/transitória

Estrutura de erro atual segue o corpo já retornado pelo endpoint (`detail`), mantendo compatibilidade do Optimus nesta fase.

## Observabilidade
- Logs de autorização registram:
  - `auth_type`
  - `route_path`
  - `scope_check_result`
- Uso de API key atualiza `last_used_at`.
