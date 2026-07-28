# Fluxos do projeto

Como as coisas acontecem na prática, passo a passo. Complementa
`contexto/dashboard.md` (o que cada tela mostra) com o "como se chega
lá" e "o que fazer quando".

## Fluxo: gerar o relatório de problemas recorrentes

1. Garantir `ZBX_URL` e `ZBX_TOKEN` configurados (variável de ambiente ou
   default no script — ver `prompts/politicas/configuracao.txt` sobre migrar
   para `.env`).
2. Rodar `python scripts/relatorio_problemas.py`.
3. O script busca eventos de PROBLEMA do último ano, agrega por nome de
   problema em 4 janelas (Hoje/7d/30d/365d) e gera HTML + CSV em
   `scripts/saidas/`.
4. Ler o resumo do console (Top 5 de cada janela) para uma primeira
   leitura rápida; abrir o HTML para o detalhe completo.
5. Ao identificar um padrão de ruído (ex.: caso GoogleUpdater), seguir o
   fluxo de correção abaixo.

## Fluxo: investigar e corrigir ruído de alerta recorrente

1. Rodar `relatorio_problemas.py` e identificar o problema com volume
   desproporcional.
2. Se for ligado a descoberta de serviço Windows, rodar
   `scripts/inspecionar_servicos.py` para localizar a regra de descoberta, o
   filtro atual (macro `{$SERVICE.NAME.NOT_MATCHES}`) e os hosts
   afetados.
3. Definir o regex de exclusão que cobre o padrão real (cuidado com
   variações de nome — ver armadilha documentada em `contexto/api.md`).
4. **Nunca aplicar direto.** Seguir o fluxo de escrita em produção abaixo.
5. Registrar a mudança em um ADR novo em `docs/adr/` e no
   `docs/CHANGELOG.md`, com valor antes/depois.

## Fluxo: qualquer escrita em produção no Zabbix (regra geral)

Aplica-se a qualquer chamada `*.create`, `*.update`, `*.delete` na API.

1. Implementar a mudança em um script dedicado, nunca inline numa sessão
   interativa sem registro.
2. O script SEMPRE: lê o estado atual e imprime "ANTES"; calcula o novo
   valor sem descartar o anterior (quando for um valor composto, como uma
   macro de exclusão); é idempotente (checar se a mudança já foi
   aplicada antes de reaplicar).
3. **Pedir confirmação explícita ao usuário antes de executar** (ver
   `prompts/workflow/missao.txt`, critérios de confirmação).
4. Executar, imprimir "DEPOIS", confirmar sucesso.
5. Documentar em `docs/CHANGELOG.md` e, se for uma decisão relevante, como
   um ADR novo em `docs/adr/`.

## Fluxo: onboarding de uma IA nova nesta base de código

A sequência completa e autoritativa é `AI_BOOTSTRAP.md` — este fluxo não
a repete para não divergir dela com o tempo. Resumo: `AI_BOOTSTRAP.md` →
`CLAUDE.md` → `prompts/` → `contexto/` → `docs/` → `AI_MEMORY.md` →
`prompts/workflow/roadmap.txt` → código-fonte. Ao chegar em `contexto/`,
ler em especial os arquivos relevantes ao pedido do usuário para não
repetir investigação já feita (ex.: não redescobrir o caso GoogleUpdater
do zero — está em `docs/adr/002-correcao-ruido-googleupdater.md`).

## Fluxo: adicionar uma categoria nova de regra ou conhecimento

A regra completa está em `prompts/workflow/evolucao.txt` — este fluxo é
só o lembrete de onde o arquivo novo vai fisicamente:

1. Perceber que o assunto não se encaixa bem em nenhum prompt/contexto
   existente (forçar o assunto num arquivo errado é pior que criar um
   novo — cada prompt tem responsabilidade única, ver
   `padroes/estrutura_pastas.md`).
2. Criar `prompts/<politicas|tarefas|workflow>/nome.txt` (regra de
   desenvolvimento), `contexto/nome.md` (conhecimento factual),
   `padroes/nome.md` (convenção) ou `specs/nome.md` (especificação de
   funcionalidade), conforme o caso.
3. Atualizar a tabela de `CLAUDE.md` para incluir o arquivo novo na
   ordem de leitura.
