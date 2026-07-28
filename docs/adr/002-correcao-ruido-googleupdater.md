# ADR 002 — Corrigir ruído de eventos "GoogleUpdater" na macro do template

**Data:** 2026-07-27
**Status:** Aceito e aplicado.

## Contexto

O relatório de problemas recorrentes (`scripts/relatorio_problemas.py`)
mostrou que os eventos `GoogleUpdaterInternalService...` e
`GoogleUpdaterService...` (uma trigger criada por versão do Chrome, via
descoberta automática de serviços do Windows) representavam **~50% de
todos os eventos de problema** do ambiente Zabbix do Grupo Rancho no
último ano (~23.500 eventos totais).

Investigação com `scripts/inspecionar_servicos.py` revelou que já havia
uma tentativa manual de correção em 3 hosts (Siagri Nutrane, Siagri
Rancho, TERMINAL CAIXA02-GUS BR), adicionando a condição
`^GoogleUpdaterService.*` diretamente na regra de descoberta de cada
host — mas esse padrão não cobre `GoogleUpdaterInternalService...`
(o termo "Internal" quebra o casamento do regex), então o ruído
continuava.

## Problema

Como eliminar esse ruído de forma que cubra todas as variações de nome
do serviço (atuais e futuras, já que o instalador do Chrome cria um
serviço novo a cada versão), sem repetir o erro da correção manual
anterior e sem exigir manutenção por host?

## Alternativas avaliadas

1. **Expandir a exclusão manual em cada host** (`^GoogleUpdaterService.*`
   → incluir também `^GoogleUpdaterInternalService.*`) — descartado:
   perpetua o problema de manutenção por host; hosts novos ficariam sem a
   correção; hosts existentes já estavam inconsistentes entre si.
2. **Desabilitar as triggers já criadas, uma a uma** — descartado:
   paliativo, as triggers voltam a cada nova versão do Chrome.
3. **Desligar a descoberta de serviços inteira** — descartado: perde
   monitoramento de serviços legítimos (ex.: SQL Server) junto.
4. **Corrigir a macro `{$SERVICE.NAME.NOT_MATCHES}` nos templates**
   (`Windows by Zabbix agent` e `...active`), acrescentando
   `GoogleUpdater.*` ao valor já existente — escolhida.

## Decisão tomada

Aplicar, via API (`usermacro.update`), o acréscimo de `GoogleUpdater.*`
ao valor atual da macro `{$SERVICE.NAME.NOT_MATCHES}` nos dois templates,
preservando integralmente as exclusões de fábrica já presentes. Script
`scripts/aplicar_exclusao_googleupdater.py` criado para isso, com leitura
do estado atual, cálculo do novo valor sem descartar o anterior, e
impressão de antes/depois — confirmado com o usuário antes de executar.

- **Antes:** `^(?:RemoteRegistry|MMCSS|gupdate|SysmonLog|clr_optimization_v.+|sppsvc|gpsvc|Pml Driver HPZ12|Net Driver HPZ12|MapsBroker|IntelAudioService|Intel\(R\) TPM Provisioning Service|dbupdate|DoSvc|CDPUserSvc_.+|WpnUserService_.+|OneSyncSvc_.+|WbioSrvc|BITS|tiledatamodelsvc|GISvc|ShellHWDetection|TrustedInstaller|TabletInputService|CDPSvc|wuauserv|edgeupdate|cbdhsvc_.+)$`
- **Depois:** o mesmo valor com `|GoogleUpdater.*` inserido antes de `)$`.

## Justificativa

Corrigir no nível de template (não de host) resolve para todos os hosts
que usam esse template, de uma vez, incluindo hosts futuros. O padrão
`GoogleUpdater.*` (sem exigir "Service" logo em seguida) cobre qualquer
variação de nome que o instalador venha a criar.

## Consequências

- Nova descoberta (~1x/hora) para de criar triggers desse padrão; as
  existentes são removidas conforme retenção de "recurso perdido" da LLD.
- As exclusões manuais nos 3 hosts tornaram-se redundantes, mas não
  foram removidas — candidato de limpeza em `prompts/workflow/roadmap.txt`.
- Padrão estabelecido para o próximo ruído recorrente identificado:
  investigar a causa raiz na configuração de descoberta antes de
  silenciar no nível de trigger/notificação.
