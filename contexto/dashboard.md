# Dashboard e relatórios — estado e propósito de cada visão

Registro do que cada relatório/tela deste projeto mostra e por que ela
existe — para não recriar a mesma visão com nome diferente, e para
qualquer IA saber rapidamente "qual script eu uso para responder essa
pergunta do usuário".

## Dashboard nativo do Zabbix (não é deste projeto, mas é o ponto de
partida)

O Zabbix já tem um dashboard "Visão global" nativo com: hosts por CPU,
gauges de utilização, gráficos de pizza de disco, mapa de disponibilidade
por grupo, lista de problemas atuais. Ele responde **"o que está
acontecendo agora"**. Este projeto existe para responder a pergunta que
o dashboard nativo não responde bem: **"o que se repete e piora ao longo
do tempo"** (ver `prompts/workflow/missao.txt`).

## `scripts/relatorio_problemas.py` — Relatório de problemas recorrentes

- **Pergunta que responde:** quais problemas mais se repetem, em Hoje /
  7 dias / 30 dias / 365 dias?
- **Fonte:** `event.get` (eventos de PROBLEMA, `value=1`).
- **Saída:** `scripts/saidas/relatorio_problemas_AAAAMMDD_HHMM.html` (visual,
  imprimível) e `.csv` (dados brutos para Excel/análise).
- **Regra de agregação:** ver `contexto/regras_negocio.md`.
- **Uso real já feito:** identificou que ~50% dos eventos em 2026-07 eram
  ruído do GoogleUpdater (ver `docs/adr/002-correcao-ruido-googleupdater.md`).

## `scripts/validar_token.py` — Validação de token de API

- **Pergunta que responde:** meu token do Zabbix está funcionando, e com
  qual usuário/permissão?
- Não gera relatório, é uma ferramenta de diagnóstico/onboarding.

## `scripts/inspecionar_servicos.py` — Inspeção de descoberta de serviços
Windows

- **Pergunta que responde:** qual é a regra de descoberta (LLD) de
  serviços do Windows, qual o filtro atual, e onde estão as triggers de
  um serviço específico (usado para investigar o ruído do GoogleUpdater)?
- Somente leitura.

## `scripts/aplicar_exclusao_googleupdater.py` — Correção de configuração

- **O que faz:** acrescenta `GoogleUpdater.*` à macro
  `{$SERVICE.NAME.NOT_MATCHES}` nos templates `Windows by Zabbix agent` e
  `...active`, preservando o valor anterior. Idempotente.
- **Não é um script de uso recorrente** — foi uma correção pontual. Fica
  no projeto como referência de como aplicar correções de configuração
  com segurança (antes/depois, idempotência — ver
  `prompts/tarefas/backend.txt` e `prompts/politicas/seguranca.txt`).

## Visões ainda não implementadas (ver `prompts/workflow/roadmap.txt`)

- Ranking de problemas por **host** (em vez de por nome de problema) —
  responde "qual equipamento me dá mais dor de cabeça?".
- Relatório de disponibilidade/SLA por host ou grupo.
- Painel Flask consolidando as visões acima com atualização automática.
- Envio automático do relatório semanal por e-mail.
