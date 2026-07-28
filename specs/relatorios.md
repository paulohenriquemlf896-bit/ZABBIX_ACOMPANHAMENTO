# Spec: Relatório de problemas recorrentes

**Status:** implementado (`scripts/relatorio_problemas.py`). Esta spec
foi escrita retroativamente para documentar o comportamento existente e
servir de referência para as próximas visões de relatório (ex.: ranking
por host — ver seção "Extensões futuras").

## Objetivo

Responder "quais problemas do ambiente monitorado mais se repetem?" em
múltiplas janelas de tempo, para diferenciar ruído crônico de
degradação real, algo que o dashboard nativo do Zabbix (focado no
"agora") não responde.

## Regras de negócio

Ver `contexto/regras_negocio.md` para as definições formais
(recorrência, agrupamento, janelas, severidade). Resumo:

- Recorrência = contagem de eventos `value=1` (entrada em PROBLEMA) por
  nome de problema.
- Agrupamento por `event.name`, não por `triggerid`.
- 4 janelas fixas: Hoje, 7 dias, 30 dias, 365 dias.
- Severidade do grupo = severidade máxima observada no período.

## Fluxo

1. Validar conectividade (`apiinfo.version`).
2. Buscar todos os eventos de PROBLEMA dos últimos 365 dias
   (`event.get`, `source=0, object=0, value=1`, com `limit=MAX_EVENTOS`).
3. Para cada uma das 4 janelas, filtrar os eventos por `clock >= desde` e
   agregar.
4. Gerar HTML (visual, uma `<section>` por janela) e CSV (dados
   consolidados de todas as janelas).
5. Imprimir no console um resumo (Top 5 de cada janela).

## Entradas

| Nome | Origem | Obrigatório | Observação |
|---|---|---|---|
| `ZBX_URL` | variável de ambiente | sim | endpoint da API |
| `ZBX_TOKEN` | variável de ambiente | sim | token com permissão de leitura |
| `MAX_EVENTOS` | constante no topo do script | não (tem default) | teto de eventos buscados |
| `TOP_N` | constante no topo do script | não (tem default) | itens exibidos por ranking |

## Saídas

- `scripts/saidas/relatorio_problemas_AAAAMMDD_HHMM.html`
- `scripts/saidas/relatorio_problemas_AAAAMMDD_HHMM.csv` — colunas:
  `periodo, problema, ocorrencias, gravidade, hosts, primeira_vez, ultima_vez`

## Validações

- `ZBX_URL`/`ZBX_TOKEN` ausentes ou inválidos → `[FALHA]` e saída com
  código != 0, sem gerar arquivo parcial.
- Resposta da API com `error` → mensagem com `data`/`message` do Zabbix,
  não um erro genérico.

## Casos extremos

- Nenhum evento no período → seção do relatório mostra
  `"Nenhum problema registrado neste período."` (nunca tabela vazia
  muda).
- Evento sem host associado → grupo aparece com "hosts" vazio, sem
  quebrar a agregação (visto na prática com triggers antigas de versões
  descontinuadas do GoogleUpdater — ver `docs/adr/002-correcao-ruido-googleupdater.md`).
- Nome de problema com caracteres HTML (`<`, `>`, `&`, `"`) → sempre
  escapado na saída HTML.
- Empate de contagem entre dois problemas → ordem estável pela ordem de
  iteração (não há critério de desempate definido além disso; se um
  critério de desempate explícito for necessário no futuro, definir aqui
  antes de implementar).
- `MAX_EVENTOS` atingido → aviso explícito no console, relatório gerado
  mesmo assim com os dados parciais.

## Extensões futuras (não implementadas — candidatas de roadmap)

- Envio automático por e-mail (ver `specs/notificacoes.md`).

## Extensões já implementadas em outra spec

- Ranking por host em vez de por nome de problema — ver
  `specs/ranking_por_host.md` (implementado no painel web).
