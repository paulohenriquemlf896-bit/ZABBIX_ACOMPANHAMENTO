# Padrão de respostas de API (painel Flask — futuro)

Ainda não há endpoints internos implementados (o painel Flask é
planejado — ver `specs/dashboard.md` e `prompts/tarefas/backend.txt`).
Este documento fixa o formato **antes** do primeiro endpoint existir,
para que todos nasçam consistentes.

## Envelope de resposta padrão

Todo endpoint JSON interno (`/api/...`) retorna sempre este formato,
sucesso ou falha:

```json
{
  "ok": true,
  "dados": { "...": "..." },
  "erro": null
}
```

Em falha:

```json
{
  "ok": false,
  "dados": null,
  "erro": "Mensagem clara em português do que deu errado"
}
```

- `ok`: booleano, sempre presente.
- `dados`: presente e não-nulo quando `ok=true`; `null` quando `ok=false`.
- `erro`: `null` quando `ok=true`; string em português, amigável ao
  usuário, quando `ok=false` — nunca stacktrace cru (ver
  `prompts/politicas/logs.txt`).

## Códigos HTTP

- `200` — requisição processada, mesmo que `ok=false` no corpo (erro de
  negócio, ex.: "host não encontrado", é um 200 com `ok=false`, não um
  4xx/5xx).
- `400` — requisição malformada (parâmetro obrigatório ausente,
  querystring fora da whitelist — ver `prompts/politicas/seguranca.txt`).
- `401`/`403` — quando autenticação/autorização existir no painel
  (não implementado ainda).
- `500` — falha inesperada não tratada (deve ser raro; toda falha
  esperada vira `ok=false` com 200).

## Paginação (quando um endpoint retornar lista grande)

```json
{
  "ok": true,
  "dados": {
    "itens": [ "..." ],
    "total": 123,
    "pagina": 1,
    "por_pagina": 50
  },
  "erro": null
}
```

## Querystring

- Parâmetros de filtro validados contra whitelist (ex.:
  `periodo=hoje|7d|30d|365d`) — nunca aceitos livremente (ver
  `prompts/politicas/seguranca.txt`).
- Nomes de parâmetro em português, snake_case, coerentes com o resto do
  projeto — `periodo`, `host`, `severidade_minima`.

## Rota de saúde

```
GET /health
{"ok": true, "zabbix_alcancavel": true, "versao_api": "7.4.4", "hora_servidor": "2026-07-27T18:00:00"}
```

Ver `prompts/politicas/monitoramento.txt` para o propósito desta rota.

## Consistência com os relatórios CLI existentes

Os scripts CLI atuais não são uma API HTTP, mas seguem o mesmo espírito
de "resultado estruturado + erro claro": o padrão de prefixos de console
(`[OK]`/`[FALHA]`/...) é o equivalente funcional do envelope `ok`/`erro`
acima. Ao expor no painel Flask uma funcionalidade que hoje é um script
CLI, reaproveitar a mesma lógica de dados (camada de domínio) e só trocar
a camada de apresentação — nunca duplicar a lógica (ver
`prompts/politicas/principios.txt`, item 2).
