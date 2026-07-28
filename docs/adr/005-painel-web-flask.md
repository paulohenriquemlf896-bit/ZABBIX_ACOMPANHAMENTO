# ADR 005 — Iniciar o painel web com Flask, servido por waitress

**Data:** 2026-07-28
**Status:** Aceito e em implementação (escopo inicial — ver `specs/dashboard.md`).

## Contexto

O projeto até aqui gera relatórios como arquivos HTML/CSV estáticos via
`scripts/relatorio_problemas.py`, rodado manualmente. `specs/dashboard.md`
já definia o escopo de um painel web consolidando essas visões, mas
"planejado, não implementado". O usuário pediu explicitamente para
começar a construir o projeto e, diante das opções (painel Flask, e-mail
automático, dívidas técnicas, outro item de roadmap), escolheu o painel
web como ponto de partida.

## Problema

Como servir uma versão navegável e sempre atualizada do relatório de
problemas recorrentes, na rede interna, sem duplicar a lógica de
agregação já existente e testada em `scripts/relatorio_problemas.py`, e
seguindo a arquitetura de camadas já definida em
`prompts/politicas/arquitetura.txt` e `prompts/tarefas/backend.txt`?

## Alternativas avaliadas

1. **Servidor HTTP com só a biblioteca padrão (`http.server` +
   templating manual)** — descartado: reimplementar roteamento,
   querystring parsing e escaping de forma seguro à mão é mais código e
   mais risco de erro do que usar um framework maduro; contraria
   `prompts/politicas/dependencias.txt` apenas quando a stdlib resolve
   com esforço comparável, o que não é o caso aqui.
2. **Flask, servido pelo próprio servidor de desenvolvimento do Flask**
   — descartado como solução final: o servidor de debug do Flask não é
   apto para uso contínuo (`prompts/tarefas/backend.txt`, item 13); serve
   apenas para iteração local.
3. **Flask + waitress (produção, Windows)** — escolhida. `waitress` e
   `flask` já estavam previstos como dependências esperadas em
   `prompts/politicas/dependencias.txt`, item 2, desde antes desta
   decisão.

## Decisão tomada

- Adicionadas as dependências `flask` e `waitress` (`requirements.txt`
  criado nesta tarefa).
- Lógica de domínio (`buscar_eventos`, `agregar`, mapas de severidade,
  formatação de data) extraída de `scripts/relatorio_problemas.py` para
  `src/relatorios_service.py` — módulo compartilhado entre o script CLI
  existente e o novo painel, evitando duplicação (conforme já previsto em
  `specs/dashboard.md`, item 3).
- Estrutura do painel dentro de `src/web/`, seguindo a estrutura mínima
  definida em `prompts/tarefas/backend.txt`, item 9 (autoridade sobre o
  tema — mais específica que o padrão de blueprint por área sugerido em
  `templates/flask_blueprint.py`, reservado para quando o painel tiver
  mais de uma área/view a justificar essa divisão):
  `src/web/app.py` (criação da app, rota de página `/`, rota `/health`,
  execução via waitress), `src/web/api.py` (blueprint `bp_api` com os
  endpoints JSON internos, registrado por `app.py`),
  `src/web/services/relatorios.py` (cache de 60s sobre
  `src/relatorios_service.py`), `src/web/templates/` (Jinja2: `base.html`,
  `_componentes.html`, `index.html`).
- Escopo inicial limitado ao definido em `specs/dashboard.md`: uma visão
  (recorrência de problemas), seletor de período via querystring
  (whitelist), cache em memória de 60s, rota `/health`. Sem autenticação,
  sem escrita no Zabbix pela interface (fora de escopo desta primeira
  versão, conforme a spec).

## Justificativa

Reaproveitar `agregar()`/`buscar_eventos()` em vez de duplicá-los no
painel respeita `prompts/politicas/principios.txt` (itens 1 e 2) e a
regra explícita da spec. Manter o escopo inicial pequeno (uma visão, sem
autenticação) respeita `prompts/politicas/principios.txt` item 8
(simplicidade) e o próprio `specs/dashboard.md` ("Fora de escopo desta
primeira versão"). `waitress` é a opção já indicada pelo projeto para
servir em produção no Windows, evitando expor o servidor de debug do
Flask (risco de segurança e de estabilidade sob uso contínuo).

## Consequências

- `scripts/relatorio_problemas.py` muda de import (passa a importar de
  `src/relatorios_service.py`), mas preserva 100% do comportamento
  observável (mesma saída HTML/CSV/console) — validado por execução
  manual antes/depois desta mudança.
- Primeira dependência externa do projeto além da stdlib; `requirements.txt`
  criado e deve ser mantido atualizado a partir de agora
  (`prompts/politicas/dependencias.txt`).
- `src/` deixa de conter só `zbx_api.py` e ganha uma subárvore de
  aplicação (`web/`), como já estava planejado em `src/README.md`.
- Painel roda hoje só localmente/rede interna, sem processo de
  implantação automatizado — isso é um próximo passo natural, não
  coberto por este ADR.
