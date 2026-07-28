# Spec: Ranking de problemas por host

**Status:** implementado. Extensão prevista desde
`specs/relatorios.md` ("Extensões futuras") e no roadmap de
`AI_MEMORY.md`.

## Objetivo

Responder "qual host me dá mais dor de cabeça?", em vez de "qual
problema mais se repete?" (`specs/relatorios.md`). Mesma fonte de dados
e mesmas janelas de tempo, agrupamento diferente.

## Regras de negócio

Reaproveita `contexto/regras_negocio.md` (recorrência, janelas,
severidade) com uma regra nova, específica desta visão:

- **Agrupamento por host afetado**, não por nome do problema.
- **Evento com múltiplos hosts conta para cada host envolvido.** Um
  evento raramente afeta mais de um host neste ambiente, mas quando
  afeta, cada host recebe +1 na contagem (não se divide o evento entre
  eles). Consequência aceita: a soma das ocorrências de todos os hosts
  pode ser levemente maior que o total de eventos do período — o
  percentual de cada linha ainda é correto individualmente (ocorrências
  daquele host / total de eventos), só não soma 100% na coluna inteira.
- **Evento sem host associado é excluído do ranking por host** (não há
  a quem atribuir), mas continua contando no total geral de eventos do
  período e na distribuição de severidade — só não aparece em nenhuma
  linha do ranking.
- Cada linha do ranking também lista os **nomes distintos de problema**
  que geraram ocorrências naquele host no período (mesmo papel que a
  coluna "hosts afetados" tem na visão por problema, invertido).
- Severidade da linha = severidade máxima observada nos eventos daquele
  host no período (mesma regra da visão por problema).

## Fluxo

1. Reaproveita `buscar_eventos()` (mesmos eventos já buscados para a
   visão por problema no mesmo período — nenhuma consulta extra à API).
2. Nova função `agregar_por_host()` em `src/relatorios_service.py`,
   espelhando `agregar()` mas com a chave de agrupamento trocada.
3. Página do painel (`src/web/app.py`) e endpoint JSON
   (`src/web/api.py`) ganham o parâmetro `visao` (`problema` — default,
   `host`), validado contra whitelist, combinável com `periodo` na
   querystring (`?periodo=7d&visao=host`).
4. Cache do painel (`src/web/services/relatorios.py`) passa a ser
   chaveado por `(periodo, visao)`.

## Entradas

| Nome | Origem | Obrigatório | Observação |
|---|---|---|---|
| `visao` | querystring (painel) | não (default `problema`) | whitelist: `problema`, `host` |

## Saídas

- Página `/` com seletor de visão além do seletor de período já
  existente.
- `GET /api/relatorios/dados?periodo=...&visao=host` — mesmo envelope
  `ok/dados/erro`; item do `ranking` tem `host`/`problemas` em vez de
  `nome`/`hosts` (ver `src/web/services/relatorios.py`).

## Validações

- `visao` fora da whitelist → cai no default `problema`, nunca erro 500
  (mesma regra já aplicada a `periodo`).

## Casos extremos

- Nenhum evento no período → ranking por host vazio, mesma mensagem
  "Nenhum problema registrado neste período" (reaproveitada).
- Todos os eventos sem host → ranking por host vazio mesmo com total >
  0 (diferença visível entre "Total" da distribuição de severidade e a
  ausência de linhas no ranking — aceito, não é bug).
- Host aparece em janelas menores mas não nas maiores (ou vice-versa) →
  comportamento normal de janela de tempo, mesma lógica já usada na
  visão por problema.

## Fora de escopo desta versão

- Cruzamento com inventário (GLPI) para mostrar hosts sem nenhum
  problema no período — candidato de roadmap separado
  (`contexto/integracoes.md`).
