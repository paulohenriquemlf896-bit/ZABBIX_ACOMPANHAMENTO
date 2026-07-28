# Spec: Histórico de ocorrências (drill-down)

**Status:** implementado. Pedido do usuário em 2026-07-28, motivado por
uma investigação real feita ao vivo contra a API (host Siagri Nutrane,
trigger "Acesso Nutrane está fora do ar" — ver `docs/CHANGELOG.md` e
`contexto/servidores.md`).

## Objetivo

Responder, para uma linha específica do ranking (um problema, na visão
"por problema", ou um host, na visão "por host"): **quando cada
ocorrência começou, quando terminou, e quanto durou** — em vez de só a
contagem agregada que `scripts/relatorio_problemas.py` e o painel já
mostravam. Não substitui o ranking; é um drill-down a partir dele.

## Regras de negócio

- Uma ocorrência é um evento de PROBLEMA (`value=1`) já usado pelo
  ranking. "Resolvida" significa que o Zabbix registrou o evento de
  recuperação associado (`r_eventid != "0"`); o horário de resolução é
  o `clock` desse evento de recuperação, buscado à parte (a API do
  Zabbix não devolve `r_clock` diretamente em `event.get`, só
  `r_eventid` — descoberto na prática ao implementar isto, registrado
  em `contexto/api.md`).
- Ocorrência sem `r_eventid` (ainda `"0"`) aparece como **"ainda
  aberta"** — sem hora de fim, sem duração.
- O agrupamento do drill-down usa **a mesma chave que o ranking já
  usa** (nome do problema na visão "problema", host afetado na visão
  "host" — ver `contexto/regras_negocio.md` e `specs/ranking_por_host.md`),
  para o total de ocorrências do histórico bater exatamente com o
  número mostrado na linha do ranking que originou o clique.
- Reaproveita os mesmos eventos já buscados para o ranking do período
  (`buscar_eventos()`) — não é uma segunda consulta de eventos de
  problema à API, só uma filtragem em memória pela chave. Só busca algo
  novo na API para descobrir os horários de resolução (uma chamada
  `event.get` pelos `r_eventid` do grupo, não do período inteiro).

## Fluxo

1. Usuário clica no nome do problema (ou host) numa linha do ranking no
   painel.
2. Painel busca os eventos do período (igual ao ranking), filtra pela
   chave clicada (`eventos_do_grupo()`), busca os horários de resolução
   dos eventos filtrados (`buscar_resolucoes()`), monta a lista
   ordenada do mais recente para o mais antigo (`historico()`) — tudo
   em `src/relatorios_service.py`.
3. Página mostra: resumo (total, quantas ainda abertas, duração
   média/mínima/máxima), um mini-gráfico de ocorrências por dia (ajuda
   a identificar dias de pico — foi exatamente isso que motivou o
   pedido), e a tabela detalhada de cada ocorrência.

## Entradas

| Nome | Origem | Obrigatório | Observação |
|---|---|---|---|
| `periodo` | querystring | não (default `7d`) | mesma whitelist do ranking |
| `visao` | querystring | não (default `problema`) | mesma whitelist do ranking |
| `chave` | querystring | sim | nome do problema ou host; sem
  whitelist possível (é texto livre do Zabbix) — validado só por
  tamanho máximo (500 caracteres, `prompts/politicas/seguranca.txt`
  item 9) |

## Saídas

- Página `/historico?periodo=...&visao=...&chave=...`.
- `GET /api/relatorios/historico?periodo=...&visao=...&chave=...` —
  envelope `ok/dados/erro` (`padroes/padrao_respostas_api.md`),
  `dados.itens` é a lista de ocorrências.

## Validações

- `chave` ausente ou vazia → mensagem amigável, nunca 500 (página) /
  400 (API).
- `chave` maior que 500 caracteres → tratada como inválida (mesma
  resposta de "ausente").
- `chave` que não corresponde a nada no período → lista vazia, mensagem
  "Nenhuma ocorrência encontrada", não é erro.

## Casos extremos

- Todas as ocorrências do grupo ainda abertas (sem `r_eventid`) → sem
  estatística de duração (não dividir por zero), mensagem indicando que
  nenhuma foi resolvida ainda.
- Uma única ocorrência → gráfico por dia com uma barra só (não é
  anti-padrão de gráfico, é informação real).
- Falha ao buscar os horários de resolução (erro de rede na segunda
  chamada) → degrada graciosamente: mostra as ocorrências sem duração
  (fim/duração em branco) em vez de falhar a página inteira — a
  informação de quando caiu ainda é mostrada mesmo se "quando voltou"
  falhar.

## Fora de escopo desta versão

- Anotações manuais por ocorrência (ex.: "causa: manutenção
  programada") — exigiria persistência própria, fora do escopo atual
  (`prompts/tarefas/banco_de_dados.txt`: só criar banco com necessidade
  real).
- Correlação automática entre dias de pico e eventos externos (backup,
  janela de manutenção) — análise humana, não automatizada aqui.
