# Servidores e hosts monitorados

Inventário de conhecimento sobre os hosts que aparecem nos relatórios
deste projeto. Não é um espelho completo do Zabbix (isso seria
redundante e ficaria desatualizado) — é o registro do que já foi
**observado e investigado** sobre cada um, para não redescobrir a cada
sessão.

## Hosts com histórico de problema investigado

### SRV-FORTES
Aparece recorrentemente em quase todas as categorias de alerta: memória
alta, uso de swap, disco lento (tempo de resposta de leitura/escrita
elevado), CPU privilegiada alta, "Memory Pages/sec" alto. Padrão sugere
**servidor sobrecarregado** — candidato a investigação de capacidade
(upgrade de RAM/disco ou revisão de carga de trabalho). Ainda não
investigado a fundo (item de roadmap).

### Siagri Nutrane
Host da aplicação Nutrane. Gera os alertas "Acesso Nutrane está fora do
ar" e "Acesso remoto Siagri Nutrane indisponível" com frequência
crescente (55x em 7 dias observados em 2026-07-27, tendência de piora).
Também foi um dos hosts com a correção manual incompleta de exclusão do
GoogleUpdater (ver `docs/adr/002-correcao-ruido-googleupdater.md`).

**Investigação de "Acesso Nutrane está fora do ar" feita em 2026-07-28**
(via `specs/historico_ocorrencias.md`, usando o histórico de
início/resolução de cada ocorrência): 169 ocorrências em 30 dias, **100%
já resolvidas sozinhas** (nenhuma ficou em aberto) — duração média de
44s, mínima de 7s, máxima de ~1h16min (um único caso fora da curva). Ou
seja, **não é uma indisponibilidade sustentada, é flapping** (a trigger
cai e volta rapidamente, de forma repetida). Dias com pico bem acima da
média: 30/06 (11x), 06/07 (23x), 18/07 (14x), 26/07 (25x) — vale
verificar se coincidem com alguma rotina/job agendado no lado da
aplicação Nutrane ou da rede até esse host; não investigado ainda.
Continua sendo candidato de investigação de estabilidade da
aplicação/rede, mas agora com hipótese mais específica (flapping
intermitente, não queda prolongada).

### Siagri Rancho
Também teve exclusão manual incompleta de GoogleUpdater. Aparece em
alertas de CPU privilegiada alta.

### Catracas (C.Alves, Carpina, Pesqueira, Teresina)
Grupo de dispositivos com alta incidência de "ICMP Ping: Unavailable" e
"High ICMP ping loss/response time" — indicativo de instabilidade de
link ou energia nesses pontos. Não investigado a fundo ainda (roadmap).

### LINK-INTERNET-WAN
Gera "WAN OFFLINE" e "Alta perda de pacotes" — provável instabilidade de
operadora de internet. Fora do controle direto do Grupo Rancho (depende
de fornecedor externo), mas vale acompanhar recorrência para eventual
cobrança de SLA.

### Zabbix server (o próprio servidor de monitoramento)
Gera "Utilization of unreachable poller processes over 75%" com volume
muito alto (o problema isolado mais recorrente do ambiente em 2026-07).
Sintoma de fila de pollers saturada por hosts inacessíveis (catracas,
dispositivos SNMP intermitentes) — tratado como sintoma derivado dos
problemas de rede acima, não causa própria. Ver
`prompts/politicas/performance.txt` e considerar ajuste de
`StartPollersUnreachable` no `zabbix_server.conf` como mitigação
complementar (não aplicado ainda — fora do escopo de acesso deste
projeto, que fala só com a API, não com o SO do servidor Zabbix).

### TERMINAL CAIXA0x (Caruaru, Gus Centro, Gus BR)
Terminais de caixa em diferentes lojas. Também afetados pelo ruído do
GoogleUpdater (ex.: TERMINAL CAIXA02-CARUARU, TERMINAL CAIXA02-GUS BR).

## Convenção de nomenclatura observada no Zabbix

Nomes de host misturam padrões (`SRV-FORTES` maiúsculo com hífen,
`Siagri Nutrane` capitalizado com espaço, `TERMINAL CAIXA02-GUS BR` todo
maiúsculo). Este projeto **não normaliza** esses nomes — reproduz
exatamente como vêm da API, para não criar uma segunda fonte de nomes
divergente do Zabbix.
