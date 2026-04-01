# Frontend build notes

## Requisitos
- Node 20+
- npm 10+
- Acesso ao registry npm permitido pela política de rede do ambiente

## Comandos
```bash
npm install
npm run build
```

## Erro comum: `vite: not found`
Esse erro ocorre quando as dependências não foram instaladas (falta `node_modules/.bin/vite`).

### Checklist
1. Verifique acesso ao registry npm
2. Rode `npm install`
3. Rode `npm run build`

## Observação
Em ambientes com política corporativa/proxy bloqueando npm (`403 Forbidden`), o build não fecha até liberar o registry ou configurar mirror autorizado.
