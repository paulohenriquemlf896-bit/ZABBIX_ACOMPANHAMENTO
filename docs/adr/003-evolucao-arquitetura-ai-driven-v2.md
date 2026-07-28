# ADR 003 — Evoluir para ecossistema de desenvolvimento orientado por IA (v2)

**Data:** 2026-07-27
**Status:** Aceito e aplicado.

## Contexto

A estrutura inicial (ver [ADR 001](001-estrutura-conhecimento-orientada-por-ia.md))
resolveu o problema de continuidade entre sessões com `prompts/` (22
arquivos numerados, plano) e `contexto/`. O projeto, porém, ainda estava
em fase muito inicial (4 scripts CLI) e o usuário definiu explicitamente
uma visão de maior prazo: um ecossistema completo onde a IA atua também
como arquiteta, revisora técnica e guardiã de qualidade, com reutilização
de código/templates, especificação prévia de funcionalidades complexas e
registro formal de decisões.

## Problema

A estrutura v1 tinha limitações identificadas pelo próprio usuário:

1. `prompts/` em lista plana (00-21) misturava, no mesmo nível, regra
   permanente (segurança, arquitetura) com regra específica de tarefa
   (backend, frontend) e regra de processo (checklist, release) — sem
   diferenciação estrutural entre elas.
2. Não havia lugar para **modelos de código reutilizáveis** — risco de
   copiar/colar padrões (ex.: cliente de API, template HTML) em vez de
   reutilizar.
3. Não havia lugar para **decisões de convenção não-código** (nomenclatura,
   estrutura de pastas, formato de resposta de API) separado do
   conhecimento factual do projeto.
4. `contexto/decisoes.md` era um único arquivo acumulando todas as
   decisões arquiteturais — cresceria sem limite e misturava registro
   histórico com estado corrente.
5. Não havia memória persistente explícita de features
   implementadas/em andamento/futuras, dívidas técnicas e riscos —
   ficava implícito em vários arquivos.
6. Não havia ordem de bootstrap explícita para uma IA nova.
7. `src/` misturava scripts utilitários com o conceito de "aplicação",
   sem separar o que é produto contínuo do que é ferramenta pontual.
8. Funcionalidades complexas podiam ser implementadas sem especificação
   prévia registrada.

## Alternativas avaliadas

1. **Manter a lista plana de prompts e só adicionar os itens novos**
   (templates, padroes, specs, examples, ADR, AI_MEMORY, AI_BOOTSTRAP)
   sem reorganizar `prompts/` — descartado: o usuário pediu
   explicitamente a categorização em `politicas/tarefas/workflow`, e
   manter os dois esquemas de organização (numeração plana convivendo
   com categorias) geraria inconsistência.
2. **Substituir `contexto/decisoes.md` por ADRs mas manter tudo mais
   igual** — parcial: resolve o item 4, mas não os demais.
3. **Reorganização completa conforme especificação do usuário** —
   escolhida.

## Decisão tomada

- `prompts/` reorganizado em três subpastas por responsabilidade:
  `politicas/` (regra sempre válida, independente da tarefa — 13
  arquivos, incluindo o novo `principios.txt`), `tarefas/` (regra por
  área — 5 arquivos) e `workflow/` (processo — 6 arquivos, incluindo o
  novo `evolucao.txt`). Prefixo numérico removido dos nomes de arquivo
  (a pasta categoriza; numeração perdeu função).
- `templates/` criado com 6 modelos reutilizáveis de código/HTML
  (`api_service.py`, `flask_blueprint.py`, `email.html`, `dashboard.html`,
  `logging.py`, `teste_unitario.py`), com marcações `TEMPLATE:` indicando
  o que adaptar.
- `padroes/` criado com 5 documentos de convenção não-código
  (`nomenclatura.md`, `estrutura_pastas.md`, `padrao_respostas_api.md`,
  `convencoes.md`, `boas_praticas.md`).
- `docs/adr/` criado; `contexto/decisoes.md` migrado para ADRs
  individuais (este documento é um deles) e reduzido a um índice/ponteiro.
- `specs/` criado para especificação de funcionalidades antes da
  implementação.
- `examples/` criado com payloads e saídas reais do projeto.
- `AI_MEMORY.md` e `AI_BOOTSTRAP.md` criados na raiz.
- `src/` (scripts utilitários) e `scripts/` (aplicação) separados: os 4
  scripts existentes (`validar_token.py`, `relatorio_problemas.py`,
  `inspecionar_servicos.py`, `aplicar_exclusao_googleupdater.py`) são
  ferramentas pontuais → movidos para `scripts/`; `src/` fica reservado
  para a futura aplicação contínua (painel Flask, cliente de API
  compartilhado).
- `CLAUDE.md` reescrito com a nova tabela de prompts por categoria,
  fluxo de bootstrap referenciando `AI_BOOTSTRAP.md`, e a regra explícita
  de verificar reutilização antes de criar código novo.

## Justificativa

A categorização de `prompts/` torna explícito o tipo de cada regra
(sempre válida vs. específica de área vs. processo), o que ajuda a IA a
aplicar a regra certa mais rápido e reduz a chance de tratar uma regra de
processo como se fosse política de segurança (ou vice-versa). `templates/`
e `padroes/` operacionalizam o princípio de "reutilizar antes de
reimplementar" — sem um lugar físico para o padrão, ele só existe como
intenção. ADRs individuais escalam melhor que um arquivo único de
decisões e deixam claro o histórico (inclusive decisões superadas, como
esta reorganiza a v1 sem apagar seu registro). `src/` vs `scripts/`
formaliza uma distinção que já existia na prática mas não estava
nomeada, evitando que a futura aplicação Flask nasça misturada com
scripts de manutenção.

## Consequências

- Toda referência cruzada dentro de `prompts/*.txt`, `contexto/*.md` e
  `docs/*.md` ao formato antigo (`prompts/NN_nome.txt`) foi atualizada
  para o novo caminho categorizado.
- Scripts existentes continuam funcionando sem alteração de código (o
  caminho de saída `saidas/` é relativo ao próprio arquivo, então mover
  de `src/` para `scripts/` não quebrou nada).
- Overhead de manutenção aumentou (mais arquivos, mais pastas) — aceito
  conscientemente como o custo de um projeto que pretende crescer para
  painel web, banco próprio e notificações automatizadas; reavaliar se o
  projeto permanecer pequeno por muito tempo sem crescer (ver
  `prompts/politicas/principios.txt`, item 8, simplicidade).
- `AI_MEMORY.md` passa a ser o lugar único para o estado corrente
  (features implementadas/em andamento/futuras, dívidas, riscos), que
  antes estava espalhado em `contexto/decisoes.md`.
